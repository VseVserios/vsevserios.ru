#!/bin/sh
set -e

if [ -n "$DATABASE_URL" ]; then
python - <<'PY'
import os
import time

import psycopg

dsn = os.environ.get("DATABASE_URL")
deadline = time.time() + 60

while True:
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        break
    except Exception as e:
        if time.time() > deadline:
            raise
        time.sleep(1)
PY
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-3}
