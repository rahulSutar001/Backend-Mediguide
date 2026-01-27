#!/bin/sh
set -e

# Debug: Print all environment variables
echo "=== Environment Variables ==="
env | grep -i port || echo "No PORT variable found"
echo "==========================="

# Use PORT from environment, default to 8080 if not set
ACTUAL_PORT=${PORT:-8080}

echo "Starting uvicorn on port: $ACTUAL_PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port $ACTUAL_PORT
