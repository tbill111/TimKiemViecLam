#!/bin/sh
set -eu
superset db upgrade
admin_user="${SUPERSET_ADMIN_USER:-admin}"
if superset fab list-users | awk 'NR > 2 { print $2 }' | grep -Fqx "$admin_user"; then
  echo "Superset admin user '$admin_user' already exists."
else
  superset fab create-admin \
    --username "$admin_user" \
    --firstname SmartCareer \
    --lastname Admin \
    --email "${SUPERSET_ADMIN_EMAIL:-admin@smartcareer.vn}" \
    --password "${SUPERSET_ADMIN_PASSWORD:?Set SUPERSET_ADMIN_PASSWORD}"
fi
superset init
exec superset run -h 0.0.0.0 -p 8088 --with-threads
