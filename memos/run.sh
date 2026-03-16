#!/bin/sh
set -e

echo "Starting Memos..."
echo "Data directory: ${MEMOS_DATA}"
echo "Port: ${MEMOS_PORT}"

# Ensure data directory exists
mkdir -p "${MEMOS_DATA}"

# Start memos
exec /usr/local/memos/memos --data "${MEMOS_DATA}" --port "${MEMOS_PORT}"
