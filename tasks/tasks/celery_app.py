# tasks/celery_app.py

from celery import Celery
import os

# Configuration details (adjust broker/backend to your actual setup, e.g., Redis or RabbitMQ)
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Initialize the Celery application
celery_app = Celery(
    'quality_check_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    # Direct Celery to find the tasks in the tasks.py file
    include=['tasks.tasks'] 
)

# Optional configuration updates
celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
    timezone='UTC'
)
