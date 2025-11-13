FROM frappe/bench:latest

WORKDIR /home/frappe

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

USER frappe

# Initialize bench
RUN bench init --skip-redis-config-generation --frappe-branch version-15 frappe-bench

WORKDIR /home/frappe/frappe-bench

# Get LMS app
RUN bench get-app lms https://github.com/frappe/lms.git

# Copy startup script
COPY --chown=frappe:frappe railway-start.sh /home/frappe/frappe-bench/railway-start.sh
RUN chmod +x /home/frappe/frappe-bench/railway-start.sh

# Expose port
EXPOSE 8000

CMD ["/bin/bash", "/home/frappe/frappe-bench/railway-start.sh"]
