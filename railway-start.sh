#!/bin/bash#!/bin/bash

set -e

# Railway startup script for Frappe LMS

echo "Starting Frappe LMS on Railway..."

set -e

cd /home/frappe/frappe-bench

# Set default values

# Extract database credentials from DATABASE_URLexport FRAPPE_SITE_NAME_HEADER=${FRAPPE_SITE_NAME_HEADER:-$RAILWAY_PUBLIC_DOMAIN}

DB_HOST=$(echo $DATABASE_URL | sed -E 's|.*@([^:]+):.*|\1|')export PORT=${PORT:-8000}

DB_PORT=$(echo $DATABASE_URL | sed -E 's|.*:([0-9]+)/.*|\1|')

DB_NAME=$(echo $DATABASE_URL | sed -E 's|.*/([^?]+).*|\1|')# Wait for database to be ready

DB_USER=$(echo $DATABASE_URL | sed -E 's|.*://([^:]+):.*|\1|')echo "Waiting for database connection..."

DB_PASS=$(echo $DATABASE_URL | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')while ! nc -z $(echo $DATABASE_URL | sed 's/.*@\([^:]*\).*/\1/') $(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/'); do

  sleep 1

SITE_NAME=${RAILWAY_PUBLIC_DOMAIN:-"site1.localhost"}done

echo "Site: $SITE_NAME"

# Extract database credentials from DATABASE_URL

# Create common_site_config.jsonDB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')

cat > sites/common_site_config.json << EOFDB_PASS=$(echo $DATABASE_URL | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')

{DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')

  "db_host": "$DB_HOST",DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')

  "db_port": $DB_PORT,DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')

  "db_type": "postgres",

  "redis_cache": "$REDIS_URL",# Configure Frappe

  "redis_queue": "$REDIS_URL",echo "Configuring Frappe for Railway..."

  "redis_socketio": "$REDIS_URL"

}# Set configuration

EOFbench set-config -g db_host $DB_HOST

bench set-config -g db_port $DB_PORT

# Create site if it doesn't existbench set-config -g db_name $DB_NAME

if [ ! -d "sites/$SITE_NAME" ]; thenbench set-config -g db_password $DB_PASS

  echo "Creating new site..."

  bench new-site $SITE_NAME \# Configure Redis

    --db-type postgres \if [ ! -z "$REDIS_URL" ]; then

    --db-host "$DB_HOST" \    bench set-config -g redis_cache "$REDIS_URL"

    --db-port "$DB_PORT" \    bench set-config -g redis_queue "$REDIS_URL"

    --db-name "$DB_NAME" \    bench set-config -g redis_socketio "$REDIS_URL"

    --db-password "$DB_PASS" \fi

    --admin-password admin \

    --no-mariadb-socket# Set site name

  if [ ! -z "$FRAPPE_SITE_NAME_HEADER" ]; then

  bench --site $SITE_NAME install-app lms    SITE_NAME=$FRAPPE_SITE_NAME_HEADER

fielse

    SITE_NAME="site1.local"

# Set as current sitefi

echo $SITE_NAME > sites/currentsite.txt

# Create site if it doesn't exist

# Start Frappeif [ ! -d "sites/$SITE_NAME" ]; then

bench serve --port ${PORT:-8000} --host 0.0.0.0    echo "Creating site: $SITE_NAME"

    bench new-site $SITE_NAME --admin-password admin --db-name $DB_NAME --force
    
    # Install LMS app
    echo "Installing LMS app..."
    bench --site $SITE_NAME install-app lms
    
    # Set site as default
    echo $SITE_NAME > sites/currentsite.txt
fi

# Migrate if needed
echo "Running migrations..."
bench --site $SITE_NAME migrate

# Start the application
echo "Starting Frappe LMS on port $PORT..."
bench serve --port $PORT --host 0.0.0.0