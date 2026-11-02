#!/bin/sh
set -eu
superset db upgrade
superset fab create-admin \
  --if-not-exists \
  --username "${SUPERSET_ADMIN_USER:-admin}" \
  --firstname SmartCareer \
  --lastname Admin \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@smartcareer.vn}" \
  --password "${SUPERSET_ADMIN_PASSWORD:?Set SUPERSET_ADMIN_PASSWORD}"
superset init
exec superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger
