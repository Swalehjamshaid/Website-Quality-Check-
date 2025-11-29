# tasks/celery_app.py

from celery import Celery
import os

# Configuration details (adjust as needed for your environment)
# For local testing, Redis is a common broker/backend.
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Initialize the Celery application
celery_app = Celery(
    'quality_check_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    # This is crucial: Tell Celery where to find the task definitions
    include=['tasks.tasks'] 
)

# Optional: Configuration updates
celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
    timezone='UTC' # Set a standard timezone
)
