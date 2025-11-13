#!/bin/bash
set -e

echo "Starting Frappe LMS on Railway..."
cd /home/frappe/frappe-bench

# Extract database credentials
DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')
DB_PASS=$(echo $DATABASE_URL | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')
DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')
DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')
DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')

SITE_NAME=${RAILWAY_PUBLIC_DOMAIN:-"site1.local"}
PORT=${PORT:-8000}

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

# Create site
if [ ! -d "sites/$SITE_NAME" ]; then
    echo "Creating site $SITE_NAME..."
    bench new-site $SITE_NAME \
        --db-type postgres \
        --db-host "$DB_HOST" \
        --db-port "$DB_PORT" \
        --db-name "$DB_NAME" \
        --db-password "$DB_PASS" \
        --admin-password admin \
        --no-mariadb-socket
    
    echo "Installing LMS app..."
    bench --site $SITE_NAME install-app lms
    echo $SITE_NAME > sites/currentsite.txt
fi

# Run migrations
echo "Running migrations..."
bench --site $SITE_NAME migrate

# Start server
echo "Starting on port $PORT..."
exec bench serve --port $PORT --host 0.0.0.0 --noreload --nothreading
