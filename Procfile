eb: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 300
worker: celery -A wsgi:celery worker -l info
