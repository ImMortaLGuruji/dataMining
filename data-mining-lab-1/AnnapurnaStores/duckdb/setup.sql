-- ===========================================================================
-- Annapurna Stores - DuckDB Setup & Extension Configuration
-- Configures S3/MinIO connection and attaches operational PostgreSQL masters.
-- ===========================================================================

INSTALL httpfs;
LOAD httpfs;

INSTALL postgres;
LOAD postgres;

-- MinIO S3 Credentials & Endpoint configuration
SET s3_endpoint='localhost:9000';
SET s3_access_key_id='annapurna';
SET s3_secret_access_key='annapurnapassword';
SET s3_use_ssl=false;
SET s3_url_style='path';

-- Attach PostgreSQL operational master database
-- Note: Uses localhost:5432 when connecting from host, or postgres:5432 when inside container.
ATTACH IF NOT EXISTS 'dbname=annapurna user=annapurna password=annapurnapassword host=localhost port=5432' AS pg_db (TYPE postgres);
