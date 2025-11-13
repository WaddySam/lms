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

# Configure email if SMTP variables are set
if [ ! -z "$SMTP_HOST" ]; then
    echo "Configuring email settings..."
    bench set-config -g mail_server "$SMTP_HOST"
    bench set-config -g mail_port "${SMTP_PORT:-587}"
    bench set-config -g use_tls "${SMTP_USE_TLS:-1}"
    bench set-config -g mail_login "$SMTP_USER"
    bench set-config -g mail_password "$SMTP_PASSWORD"
    bench set-config -g auto_email_id "${SMTP_DEFAULT_FROM:-$SMTP_USER}"
    bench set-config -g always_use_account_email_id_as_sender "0"
fi

# Set admin password from environment or use default
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}

# Check if site already exists
if [ ! -d "sites/$SITE_NAME" ]; then
    echo "Creating site $SITE_NAME..."
    bench new-site $SITE_NAME \
        --db-type postgres \
        --db-name "$DB_NAME" \
        --db-root-username "$DB_USER" \
        --db-root-password "$DB_PASS" \
        --admin-password "$ADMIN_PASSWORD" \
        --force
    
    echo "Installing LMS app..."
    bench --site $SITE_NAME install-app lms
else
    echo "Site $SITE_NAME already exists, skipping creation"
fi

echo $SITE_NAME > sites/currentsite.txt

# Run migrations
echo "Running migrations..."
bench --site $SITE_NAME migrate

# Build static assets
echo "Building static assets..."
bench --site $SITE_NAME clear-cache
bench --site $SITE_NAME clear-website-cache
bench build --apps lms

# Set up environment for serving static files
echo "Setting up environment..."
export FRAPPE_SITE=$SITE_NAME

# Start Frappe server
echo "Starting Frappe on port $PORT..."
cd /home/frappe/frappe-bench
exec bench serve --port $PORT --noreload --nothreading
