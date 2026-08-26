#!/bin/sh
set -e

python <<'PY'
"""Wait until PostgreSQL accepts connections, then optionally migrate."""
import os
import time

import psycopg

host = os.environ.get("POSTGRES_HOST", "db")
port = os.environ.get("POSTGRES_PORT", "5432")
user = os.environ.get("POSTGRES_USER", "firona")
password = os.environ.get("POSTGRES_PASSWORD", "firona")
dbname = os.environ.get("POSTGRES_DB", "firona")

for attempt in range(30):
    try:
        with psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
        ):
            break
    except Exception as exc:  # noqa: BLE001 - retry until the database is up
        print(f"Waiting for database ({attempt + 1}/30): {exc}")
        time.sleep(1)
else:
    raise SystemExit("PostgreSQL did not become ready in time")
PY

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    python manage.py migrate --noinput
    if [ "${SEED_DEMO:-0}" = "1" ]; then
        python manage.py seed_demo
    fi
fi

exec "$@"
