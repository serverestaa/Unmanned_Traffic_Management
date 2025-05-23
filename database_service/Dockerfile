FROM postgres:15

# Install PostGIS
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-15-postgis-3 \
        postgresql-15-postgis-3-scripts \
    && rm -rf /var/lib/apt/lists/*

# Create initialization script
COPY ./init-postgis.sh /docker-entrypoint-initdb.d/01-init-postgis.sh
RUN chmod +x /docker-entrypoint-initdb.d/01-init-postgis.sh

# Set default environment variables
ENV POSTGRES_DB=utm_db
ENV POSTGRES_USER=utm_user
ENV POSTGRES_PASSWORD=utm_password

EXPOSE 5432