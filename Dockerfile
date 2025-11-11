FROM frappe/bench:latest

WORKDIR /home/frappe/frappe-bench

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

USER frappe

# Get Frappe and LMS apps
RUN bench init --skip-redis-config-generation --frappe-branch version-15 frappe-bench || true
WORKDIR /home/frappe/frappe-bench

# Add LMS app from the current repository
RUN bench get-app lms https://github.com/frappe/lms.git

# Install dependencies
RUN cd apps/frappe && pip install -e .
RUN cd apps/lms && pip install -e .

# Copy startup script
COPY --chown=frappe:frappe railway-start.sh /home/frappe/frappe-bench/railway-start.sh
RUN chmod +x /home/frappe/frappe-bench/railway-start.sh

CMD ["/home/frappe/frappe-bench/railway-start.sh"]
