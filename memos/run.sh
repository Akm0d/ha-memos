#!/bin/sh
set -eu

DATA_DIR="/data"

echo "Starting Memos..."
echo "Data directory: ${DATA_DIR}"

# Create data directory if it doesn't exist
mkdir -p "${DATA_DIR}"

# Start Memos with Home Assistant's persistent add-on data directory.
exec /usr/local/memos/memos --data "${DATA_DIR}" --port 5230
