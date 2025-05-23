-- database/init-scripts/02-create-extensions.sql
-- Additional extensions and configurations for UTM system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create spatial indexes and functions if needed
-- This will be called after PostGIS is loaded

-- Function to calculate distance between two points (alternative to ST_Distance)
CREATE OR REPLACE FUNCTION calculate_distance_meters(
    lat1 DOUBLE PRECISION,
    lon1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION,
    lon2 DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
BEGIN
    RETURN ST_Distance(
        ST_Transform(ST_GeomFromText('POINT(' || lon1 || ' ' || lat1 || ')', 4326), 3857),
        ST_Transform(ST_GeomFromText('POINT(' || lon2 || ' ' || lat2 || ')', 3857)
    );
END;
$$ LANGUAGE plpgsql;

-- Function to check if point is within circular area
CREATE OR REPLACE FUNCTION point_in_circle(
    point_lat DOUBLE PRECISION,
    point_lon DOUBLE PRECISION,
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN ST_DWithin(
        ST_Transform(ST_GeomFromText('POINT(' || point_lon || ' ' || point_lat || ')', 4326), 3857),
        ST_Transform(ST_GeomFromText('POINT(' || center_lon || ' ' || center_lat || ')', 4326), 3857),
        radius_meters
    );
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO utm_user;
GRANT CREATE ON SCHEMA public TO utm_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO utm_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO utm_user;

-- Set default permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO utm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO utm_user;