#!/usr/bin/env bash

gunicorn -w 1 -b 0.0.0.0:5000 'src.app:create_app()' &
IS_CELERY_WORKER=1 celery -A src.celery_app worker --loglevel=info &
IS_CELERY_WORKER=1 celery -A src.celery_app beat --loglevel=info 