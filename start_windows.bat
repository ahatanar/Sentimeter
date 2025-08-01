@echo off
REM Windows development script for Sentimeter

REM Start the Flask application
start "Flask App" cmd /k "python -m src.app"

REM Start Celery worker
start "Celery Worker" cmd /k "set IS_CELERY_WORKER=1 && set TOKENIZERS_PARALLELISM=false && python -m celery -A src.celery_app worker --loglevel=info --pool=solo --concurrency=1"

REM Start Celery beat scheduler
start "Celery Beat" cmd /k "set IS_CELERY_WORKER=1 && python -m celery -A src.celery_app beat --loglevel=info"

echo Sentimeter started! Check the opened command windows for each component.
echo Flask App: http://localhost:5000
pause 