#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Execute the main container command (CMD in Dockerfile or command in docker-compose)
exec "$@"
