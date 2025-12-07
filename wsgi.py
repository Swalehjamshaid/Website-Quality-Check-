# wsgi.py
from app import create_app
from app.tasks import celery

application = create_app()

# Important: Initialize Celery with the app context
celery.conf.update(application.config)
