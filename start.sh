#!/usr/bin/env bash

gunicorn -w 1 -b 0.0.0.0:5000 --max-requests 1000 --max-requests-jitter 100 'src.app:create_app()'
