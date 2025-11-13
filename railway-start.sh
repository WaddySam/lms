#!/bin/bash

# Don't exit on error initially to see what fails
set +e
set -x

echo "=========================================="
echo "SCRIPT STARTED - $(date)"
echo "=========================================="
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Home directory: $HOME"
echo "PATH: $PATH"
echo "DATABASE_URL exists: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'no')"
echo "REDIS_URL exists: $([ -n "$REDIS_URL" ] && echo 'yes' || echo 'no')"
echo "PORT: ${PORT:-not set}"

# List directory contents
echo "Contents of /home/frappe:"
ls -la /home/frappe/ || echo "Failed to list /home/frappe"

echo "Contents of /home/frappe/frappe-bench:"
ls -la /home/frappe/frappe-bench/ || echo "Failed to list /home/frappe/frappe-bench"

cd /home/frappe/frappe-bench || {
    echo "FATAL: Failed to cd to /home/frappe/frappe-bench"
    exit 1
}
echo "Successfully changed to: $(pwd)"

# Re-enable exit on error
set -e

# Extract database credentials
DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')
DB_PASS=$(echo $DATABASE_URL | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')
DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')
DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')
DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')

SITE_NAME=${RAILWAY_PUBLIC_DOMAIN:-"site1.local"}
# Railway routes to port 8000 - use it directly
PORT=8000

echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo "Site: $SITE_NAME"

# Wait for database
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "Database ready!"

# Configure bench
bench set-config -g db_host $DB_HOST
bench set-config -g db_port $DB_PORT
bench set-config -g db_name $DB_NAME
bench set-config -g db_password $DB_PASS

# Configure Redis
if [ ! -z "$REDIS_URL" ]; then
    bench set-config -g redis_cache "$REDIS_URL"
    bench set-config -g redis_queue "$REDIS_URL"
    bench set-config -g redis_socketio "$REDIS_URL"
fi

# Create site - Use default Frappe behavior for database naming
if [ ! -d "sites/$SITE_NAME" ]; then
    echo "Creating site $SITE_NAME..."
    bench new-site $SITE_NAME \
        --db-type postgres \
        --admin-password admin \
        --force || echo "Site creation failed or site exists"
    
    echo "Installing LMS app..."
    bench --site $SITE_NAME install-app lms || echo "LMS already installed"
    echo $SITE_NAME > sites/currentsite.txt
fi

# Run migrations
echo "Running migrations..."
bench --site $SITE_NAME migrate

# Start server
echo "Starting on port $PORT..."
exec bench serve --port $PORT --host 0.0.0.0 --noreload --nothreading
