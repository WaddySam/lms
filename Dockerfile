FROM frappe/bench:latest

WORKDIR /home/frappe

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

USER frappe

# Initialize bench
RUN bench init --skip-redis-config-generation --frappe-branch version-15 frappe-bench

WORKDIR /home/frappe/frappe-bench

# Get LMS app
RUN bench get-app lms https://github.com/frappe/lms.git

# Clean up to reduce image size
USER root
RUN find /home/frappe/frappe-bench -type f -name "*.pyc" -delete \
    && find /home/frappe/frappe-bench -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /home/frappe/frappe-bench -type d -name ".git" -exec rm -rf {} + 2>/dev/null || true \
    && find /home/frappe/frappe-bench -type d -name "node_modules/*/test" -exec rm -rf {} + 2>/dev/null || true \
    && find /home/frappe/frappe-bench -type d -name "node_modules/*/tests" -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf /home/frappe/frappe-bench/apps/frappe/.git \
    && rm -rf /home/frappe/frappe-bench/apps/lms/.git \
    && rm -rf /home/frappe/frappe-bench/env/lib/python*/site-packages/pip* \
    && rm -rf /home/frappe/frappe-bench/logs/* \
    && rm -rf /tmp/* /var/tmp/* \
    && apt-get autoremove -y \
    && apt-get clean

USER frappe

# Copy startup script
COPY --chown=frappe:frappe railway-start.sh /home/frappe/frappe-bench/railway-start.sh
RUN chmod +x /home/frappe/frappe-bench/railway-start.sh

# Expose port
EXPOSE 8000

CMD ["/bin/bash", "/home/frappe/frappe-bench/railway-start.sh"]
