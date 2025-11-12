#!/bin/bash#!/bin/bash#!/bin/bash



set -eset -e



echo "Starting Frappe LMS on Railway..."# Railway startup script for Frappe LMS



cd /home/frappe/frappe-benchecho "Starting Frappe LMS on Railway..."



# Extract database credentials from DATABASE_URLset -e

DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')

DB_PASS=$(echo $DATABASE_URL | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')cd /home/frappe/frappe-bench

DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')

DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')# Set default values

DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')

# Extract database credentials from DATABASE_URLexport FRAPPE_SITE_NAME_HEADER=${FRAPPE_SITE_NAME_HEADER:-$RAILWAY_PUBLIC_DOMAIN}

SITE_NAME=${RAILWAY_PUBLIC_DOMAIN:-"site1.local"}

PORT=${PORT:-8000}DB_HOST=$(echo $DATABASE_URL | sed -E 's|.*@([^:]+):.*|\1|')export PORT=${PORT:-8000}



echo "Site: $SITE_NAME"DB_PORT=$(echo $DATABASE_URL | sed -E 's|.*:([0-9]+)/.*|\1|')



# Wait for databaseDB_NAME=$(echo $DATABASE_URL | sed -E 's|.*/([^?]+).*|\1|')# Wait for database to be ready

echo "Waiting for database connection..."

while ! nc -z $DB_HOST $DB_PORT; doDB_USER=$(echo $DATABASE_URL | sed -E 's|.*://([^:]+):.*|\1|')echo "Waiting for database connection..."

  sleep 1

doneDB_PASS=$(echo $DATABASE_URL | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')while ! nc -z $(echo $DATABASE_URL | sed 's/.*@\([^:]*\).*/\1/') $(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/'); do

echo "Database is ready!"

  sleep 1

# Configure Frappe

echo "Configuring Frappe..."SITE_NAME=${RAILWAY_PUBLIC_DOMAIN:-"site1.localhost"}done

bench set-config -g db_host $DB_HOST

bench set-config -g db_port $DB_PORTecho "Site: $SITE_NAME"

bench set-config -g db_name $DB_NAME

bench set-config -g db_password $DB_PASS# Extract database credentials from DATABASE_URL



# Configure Redis# Create common_site_config.jsonDB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')

if [ ! -z "$REDIS_URL" ]; then

    bench set-config -g redis_cache "$REDIS_URL"cat > sites/common_site_config.json << EOFDB_PASS=$(echo $DATABASE_URL | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')

    bench set-config -g redis_queue "$REDIS_URL"

    bench set-config -g redis_socketio "$REDIS_URL"{DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')

fi

  "db_host": "$DB_HOST",DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')

# Create site if it doesn't exist

if [ ! -d "sites/$SITE_NAME" ]; then  "db_port": $DB_PORT,DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')

    echo "Creating site: $SITE_NAME"

    bench new-site $SITE_NAME --admin-password admin --db-name $DB_NAME --force  "db_type": "postgres",

    

    echo "Installing LMS app..."  "redis_cache": "$REDIS_URL",# Configure Frappe

    bench --site $SITE_NAME install-app lms

      "redis_queue": "$REDIS_URL",echo "Configuring Frappe for Railway..."

    echo $SITE_NAME > sites/currentsite.txt

fi  "redis_socketio": "$REDIS_URL"



# Run migrations}# Set configuration

echo "Running migrations..."

bench --site $SITE_NAME migrateEOFbench set-config -g db_host $DB_HOST



# Start the applicationbench set-config -g db_port $DB_PORT

echo "Starting Frappe LMS on port $PORT..."

bench serve --port $PORT --host 0.0.0.0# Create site if it doesn't existbench set-config -g db_name $DB_NAME


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