CREATE EXTENSION IF NOT EXISTS postgis;

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

CREATE INDEX IF NOT EXISTS idx_buildings_lat_lon ON buildings(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_buildings_confidence ON buildings(confidence);
CREATE INDEX IF NOT EXISTS idx_buildings_area ON buildings(area_m2);
CREATE INDEX IF NOT EXISTS idx_buildings_geometry ON buildings USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_buildings_centroid ON buildings USING GIST(centroid);
CREATE INDEX IF NOT EXISTS idx_buildings_spatial ON buildings USING GIST(geometry);