-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create database user (if needed)
-- CREATE USER greenpulse WITH PASSWORD 'password';
-- GRANT ALL PRIVILEGES ON DATABASE greenpulse TO greenpulse;

-- Database initialization will be handled by SQLAlchemy models