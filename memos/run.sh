#!/bin/sh
set -e

DATA_DIR="/data"

echo "Starting Memos..."
echo "Data directory: ${DATA_DIR}"

# Create data directory if it doesn't exist
mkdir -p "${DATA_DIR}"

# Start memos with the data directory
exec /usr/local/memos/memos --data "${DATA_DIR}" --port 5230
