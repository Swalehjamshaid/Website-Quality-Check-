web: gunicorn app:app --bind 0.0.0.0:$PORT
worker: celery -A app.celery_app worker --loglevel=info
scheduler: celery -A app.celery_app beat --loglevel=info
