-- Initialize database for geosocial application
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions that we might need
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis" WITH SCHEMA public;

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance on location queries
-- These will be applied after tables are created by SQLAlchemy

-- Note: Actual table creation is handled by SQLAlchemy migrations
-- This file is for database-level configurations only 