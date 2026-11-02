#!/bin/bash
set -e

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 \
  --set=bi_reader_password="$BI_READER_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE bi_reader LOGIN PASSWORD %L', :'bi_reader_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bi_reader')\gexec
SQL

psql --username "$POSTGRES_USER" --dbname postgres --set=ON_ERROR_STOP=1 <<'SQL'
SELECT 'CREATE DATABASE superset_meta' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='superset_meta')\gexec
SELECT 'CREATE DATABASE smartcareer_test' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='smartcareer_test')\gexec
SQL
