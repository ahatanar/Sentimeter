import os
from dotenv import load_dotenv
load_dotenv()
from celery import Celery

celery_app = Celery('sentimeter')
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/0')),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', os.getenv('REDIS_URL', 'redis://localhost:6379/0')),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    worker_max_tasks_per_child=5,  
    worker_max_memory_per_child=450000, 
    task_acks_late=True,  
    worker_prefetch_multiplier=1,  
)

import src.tasks.enrich
import src.services.smart_scheduler
import src.services.survey_scheduler 