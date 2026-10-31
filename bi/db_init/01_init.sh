#!/bin/sh
# Chạy một lần khi khởi tạo volume PostgreSQL: tạo DB metadata cho Superset và role chỉ đọc cho dashboard.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
CREATE DATABASE superset_meta;
CREATE ROLE bi_reader LOGIN PASSWORD '${BI_READER_PASSWORD}';
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO bi_reader;
EOSQL
