#!/bin/bash
set -e

# Create the pgvector extension within the database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pgvector;
    
    -- Add any other initialization SQL statements here
    -- For example, create schemas, roles, etc.
    
    -- Example: CREATE SCHEMA IF NOT EXISTS app;
    
    SELECT 'PostgreSQL initialized with pgvector extension' as status;
EOSQL

echo "Database initialization completed."
