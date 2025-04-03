#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS pgcrypto;
  CREATE EXTENSION IF NOT EXISTS btree_gist;

  CREATE USER $POSTGRESQL_APP_USER WITH PASSWORD '$POSTGRESQL_APP_PASS';
  CREATE SCHEMA IF NOT EXISTS $APP_DB_SCHEMA;
  GRANT ALL PRIVILEGES ON SCHEMA $APP_DB_SCHEMA TO $POSTGRESQL_APP_USER;

  ALTER DEFAULT PRIVILEGES IN SCHEMA $APP_DB_SCHEMA
  GRANT ALL PRIVILEGES ON TABLES TO $POSTGRESQL_APP_USER;

  ALTER DEFAULT PRIVILEGES IN SCHEMA $APP_DB_SCHEMA
  GRANT ALL PRIVILEGES ON SEQUENCES TO $POSTGRESQL_APP_USER;

  ALTER DEFAULT PRIVILEGES IN SCHEMA $APP_DB_SCHEMA
  GRANT EXECUTE ON FUNCTIONS TO $POSTGRESQL_APP_USER;

  ALTER DATABASE "$POSTGRES_DB" SET search_path TO $APP_DB_SCHEMA;
EOSQL

echo "애플리케이션 사용자 '$POSTGRESQL_APP_USER' 및 스키마 '$APP_DB_SCHEMA' 설정 완료"