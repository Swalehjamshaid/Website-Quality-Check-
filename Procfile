web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2
worker: celery -A wsgi:celery worker --loglevel=info
beat: celery -A wsgi:celery beat --loglevel=info
