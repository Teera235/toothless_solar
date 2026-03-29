-- Initialize Toothless Solar Database
-- Create PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create buildings table
CREATE TABLE IF NOT EXISTS buildings (
    id SERIAL PRIMARY KEY,
    open_buildings_id VARCHAR(50) UNIQUE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    area_m2 DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(POLYGON, 4326),
    centroid GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_buildings_lat_lon ON buildings(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_buildings_confidence ON buildings(confidence);
CREATE INDEX IF NOT EXISTS idx_buildings_area ON buildings(area_m2);
CREATE INDEX IF NOT EXISTS idx_buildings_geometry ON buildings USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_buildings_centroid ON buildings USING GIST(centroid);

-- Create spatial index
CREATE INDEX IF NOT EXISTS idx_buildings_spatial ON buildings USING GIST(geometry);

COMMENT ON TABLE buildings IS 'Building footprints from Google Open Buildings';
COMMENT ON COLUMN buildings.open_buildings_id IS 'Unique ID from Google Open Buildings';
COMMENT ON COLUMN buildings.confidence IS 'Confidence score (0-1) from ML model';
COMMENT ON COLUMN buildings.area_m2 IS 'Building area in square meters';
COMMENT ON COLUMN buildings.geometry IS 'Building polygon geometry (WGS84)';
COMMENT ON COLUMN buildings.centroid IS 'Building centroid point (WGS84)';
