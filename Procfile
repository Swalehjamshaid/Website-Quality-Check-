web: gunicorn wsgi:application
worker: celery -A wsgi:celery worker -l info
