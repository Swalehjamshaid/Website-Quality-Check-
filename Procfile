
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A celery_worker.celery_app worker --loglevel=info
scheduler: celery -A celery_worker.celery_app beat --loglevel=info
