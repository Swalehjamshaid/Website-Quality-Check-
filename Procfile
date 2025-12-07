web: gunicorn app:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
worker: celery -A app:celery worker --loglevel=info --concurrency=1
beat: celery -A app:celery beat --loglevel=info
