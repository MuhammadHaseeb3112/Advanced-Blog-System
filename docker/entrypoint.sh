#!/bin/sh
# Container start-up. Only the web container prepares the database
# (RUN_MIGRATIONS=1); the Celery containers just start.
set -e

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput -v 0
    python manage.py set_site_domain
    if [ "${DEMO_MODE:-False}" = "True" ]; then
        python manage.py seed_demo
    fi
fi

exec "$@"
