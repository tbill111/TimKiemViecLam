#!/bin/sh
set -e
superset db upgrade
superset fab create-admin --username "${SUPERSET_ADMIN_USER:-admin}" --firstname Admin --lastname SmartCareer \
    --email admin@smartcareer.vn --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || true
superset init
exec /usr/bin/run-server.sh
