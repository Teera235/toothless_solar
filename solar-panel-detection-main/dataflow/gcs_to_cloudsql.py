"""
Apache Beam pipeline to import Google Open Buildings from BigQuery to Cloud SQL

APPROACH:
1. Load CSV files from GCS to BigQuery (fast, handles millions of rows)
2. Use Dataflow to read from BigQuery and write to Cloud SQL
3. Cloud SQL connection via Cloud SQL Proxy (not Unix socket)

USAGE:
1. First load data to BigQuery:
   bq load --source_format=CSV --skip_leading_rows=1 --autodetect \
     trim-descent-452802-t2:openbuildings.thailand_raw \
     gs://trim-descent-452802-t2-openbuildings-v3/thailand/*.csv.gz

2. Then run this pipeline:
   python gcs_to_cloudsql.py
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.io.gcp.bigquery import ReadFromBigQuery
import logging

class TransformBuilding(beam.DoFn):
    """Transform BigQuery row to Cloud SQL format"""
    
    def process(self, element):
        try:
            geometry_wkt = element.get('geometry', '')
            if not geometry_wkt or not geometry_wkt.startswith('POLYGON'):
                return
            
            # Extract coordinates for centroid
            coords_str = geometry_wkt.replace('POLYGON((', '').replace('))', '')
            coords_pairs = coords_str.split(', ')
            
            lons = []
            lats = []
            for pair in coords_pairs:
                parts = pair.strip().split()
                if len(parts) >= 2:
                    try:
                        lons.append(float(parts[0]))
                        lats.append(float(parts[1]))
                    except:
                        continue
            
            if not lons or not lats:
                return
            
            centroid_lon = sum(lons) / len(lons)
            centroid_lat = sum(lats) / len(lats)
            
            # Extract properties
            area_m2 = float(element.get('area_in_meters', 100))
            confidence = float(element.get('confidence', 0.8))
            building_id = element.get('full_plus_code', f"OB_{hash(geometry_wkt) % 10000000}")
            
            yield {
                'open_buildings_id': str(building_id),
                'latitude': centroid_lat,
                'longitude': centroid_lon,
                'area_m2': area_m2,
                'confidence': confidence,
                'geometry_wkt': geometry_wkt,
                'centroid_wkt': f"POINT({centroid_lon} {centroid_lat})"
            }
        except Exception as e:
            logging.warning(f"Failed to process row: {e}")

class WriteToCloudSQLBatch(beam.DoFn):
    """Write buildings to Cloud SQL in batches"""
    
    def __init__(self, instance_connection_name, db_name, db_user, db_password):
        self.instance_connection_name = instance_connection_name
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.conn = None
        self.cur = None
    
    def setup(self):
        """Initialize connection when worker starts"""
        import psycopg2
        
        # Parse connection name: project:region:instance
        parts = self.instance_connection_name.split(':')
        if len(parts) == 3:
            project, region, instance = parts
            # Use Cloud SQL Proxy format (available in Dataflow workers)
            host = f'/cloudsql/{self.instance_connection_name}'
        else:
            # Fallback to public IP (less secure but works)
            host = 'PUBLIC_IP_HERE'  # Replace with actual IP if needed
        
        try:
            self.conn = psycopg2.connect(
                host=host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            self.conn.set_session(autocommit=False)
            self.cur = self.conn.cursor()
            logging.info("Connected to Cloud SQL")
        except Exception as e:
            logging.error(f"Failed to connect to Cloud SQL: {e}")
            raise
    
    def process(self, batch):
        """Process a batch of buildings"""
        if not self.conn or not self.cur:
            logging.error("No database connection")
            return
        
        inserted = 0
        for building in batch:
            try:
                self.cur.execute("""
                    INSERT INTO buildings (
                        open_buildings_id,
                        latitude,
                        longitude,
                        area_m2,
                        confidence,
                        geometry,
                        centroid
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        ST_GeomFromText(%s, 4326),
                        ST_GeomFromText(%s, 4326)
                    ) ON CONFLICT (open_buildings_id) DO NOTHING;
                """, (
                    building['open_buildings_id'],
                    building['latitude'],
                    building['longitude'],
                    building['area_m2'],
                    building['confidence'],
                    building['geometry_wkt'],
                    building['centroid_wkt']
                ))
                inserted += 1
            except Exception as e:
                logging.warning(f"Failed to insert building: {e}")
                continue
        
        try:
            self.conn.commit()
            logging.info(f"Committed batch: {inserted} buildings")
        except Exception as e:
            logging.error(f"Failed to commit: {e}")
            self.conn.rollback()
    
    def teardown(self):
        """Clean up connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

def run_pipeline():
    """Run the Dataflow pipeline"""
    
    # Pipeline options
    options = PipelineOptions([
        '--project=trim-descent-452802-t2',
        '--region=asia-southeast1',
        '--runner=DataflowRunner',
        '--temp_location=gs://trim-descent-452802-t2_cloudbuild/temp',
        '--staging_location=gs://trim-descent-452802-t2_cloudbuild/staging',
        '--job_name=bigquery-to-cloudsql',
        '--max_num_workers=20',
        '--machine_type=n1-standard-2',
        '--disk_size_gb=50',
        '--setup_file=./setup.py'  # For psycopg2 dependency
    ])
    
    with beam.Pipeline(options=options) as pipeline:
        (
            pipeline
            | 'Read from BigQuery' >> ReadFromBigQuery(
                query="""
                    SELECT 
                        geometry,
                        area_in_meters,
                        confidence,
                        full_plus_code
                    FROM `trim-descent-452802-t2.openbuildings.thailand_raw`
                    WHERE geometry IS NOT NULL
                    AND geometry LIKE 'POLYGON%'
                """,
                use_standard_sql=True
            )
            | 'Transform' >> beam.ParDo(TransformBuilding())
            | 'Batch' >> beam.BatchElements(min_batch_size=100, max_batch_size=500)
            | 'Write to Cloud SQL' >> beam.ParDo(
                WriteToCloudSQLBatch(
                    'trim-descent-452802-t2:asia-southeast1:nabha-solar-db',
                    'toothless_solar',
                    'postgres',
                    'toothless_solar_2024'
                )
            )
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run_pipeline()
