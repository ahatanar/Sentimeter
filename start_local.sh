#!/usr/bin/env bash

# Local development script for macOS environments

python3 -m src.app &

IS_CELERY_WORKER=1 celery -A src.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --max-tasks-per-child=10 \
    --max-memory-per-child=300000 \
    --pool=solo \
    -E &

IS_CELERY_WORKER=1 celery -A src.celery_app beat --loglevel=info