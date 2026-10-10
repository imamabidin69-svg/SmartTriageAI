#!/bin/bash
# Membuat role aplikasi smarttriage_app. Dijalankan sekali oleh image postgres saat volume kosong.
# Hak akses ke tabel diberikan oleh migrasi Alembic, bukan oleh skrip ini, supaya aturan yang sama
# juga berlaku di basis data terkelola (Supabase) tempat role dibuat secara manual.
set -euo pipefail

psql -v ON_ERROR_STOP=1 -v role_app="$APP_DB_USER" -v password_app="$APP_DB_PASSWORD" \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'EOSQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'role_app', :'password_app')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'role_app') \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'role_app') \gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'role_app') \gexec
EOSQL
