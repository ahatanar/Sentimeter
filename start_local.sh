#!/usr/bin/env bash

# Local development script for macOS environments

# Start Flask development server
python3 -m src.app &

# Start Celery worker optimized for macOS
IS_CELERY_WORKER=1 celery -A src.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --max-tasks-per-child=10 \
    --max-memory-per-child=300000 \
    --pool=solo \
    -E &

# Start beat scheduler  
IS_CELERY_WORKER=1 celery -A src.celery_app beat --loglevel=info