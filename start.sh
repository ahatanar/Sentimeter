#!/usr/bin/env bash

gunicorn -w 1 -b 0.0.0.0:5000 --max-requests 1000 --max-requests-jitter 100 'src.app:create_app()' &

# IS_CELERY_WORKER=1 celery -A src.celery_app worker \
#     --loglevel=info \
#     --concurrency=1 \
#     --max-tasks-per-child=25 \
#     --max-memory-per-child=400000 \
#     -E &

# IS_CELERY_WORKER=1 celery -A src.celery_app beat --loglevel=info 