#!/bin/bash
set -e
# automatically export all variables (Enable this if you are running outside docker)
# set -a
# source .env.local
# set +a  # stop auto-exporting

if [ ! -f "/app/.initialized" ]; then
  echo "Running initial setup..."

  until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
    echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
    sleep 2
  done

  # Create database if not exists
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

  # Enable pgvector extension
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"

  # Create embeddings from specific JSON files (Account and Product)
  echo "Creating embeddings from JSON files..."
  for json_name in "Account"; do
    json_file="./data/json/${json_name}.json"
    if [ -e "$json_file" ]; then
      table_name=$(echo "$json_name" | tr '[:upper:]' '[:lower:]')
      echo "Processing $json_file -> $table_name"
      python json_to_pgvector.py "$json_file" "$table_name"
    else
      echo "Warning: $json_file not found"
    fi
  done

  # Debug: Check if files exist
  echo "Checking for CSV files in /data/temp/..."
  ls -la ./data/temp/ || echo "Directory /data/temp/ not found"
  echo "Current working directory: $(pwd)"
  echo "Contents of /data:"
  ls -la ./data/ || echo "Directory /data/ not found"

  # Import CSV files
  for file in ./data/temp/*.csv; do
    [ -e "$file" ] || continue
    table=$(basename "$file" .csv | tr '[:upper:]' '[:lower:]')
    echo "=== Processing: $file -> table: $table ==="

    header=$(head -n 1 "$file")
    columns=$(echo "$header" | awk -F',' '{for(i=1;i<=NF;i++) printf "%s TEXT%s", $i, (i<NF?", ":"")}')

    echo "DROP: "
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "DROP TABLE IF EXISTS $table;" && echo "SUCCESS" || echo "FAILED"
    
    echo "CREATE: "
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "CREATE TABLE $table ($columns);" && echo "SUCCESS" || echo "FAILED"
    
    echo "IMPORT: "
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\\COPY $table FROM '$file' DELIMITER ',' CSV HEADER;" && echo "SUCCESS" || echo "FAILED"
    
    echo "=== Finished $table ==="
  done

  touch /app/.initialized
else
  echo "Already initialized. Skipping setup."
fi

echo "Initialization complete. Starting main process..."
exec "$@"