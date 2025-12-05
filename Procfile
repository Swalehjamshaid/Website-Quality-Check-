web: gunicorn wsgi:application
worker: celery -A app.celery_app worker --loglevel=info
