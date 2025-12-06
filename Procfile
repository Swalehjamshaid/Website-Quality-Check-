# Web process: Runs the Flask app via Gunicorn
web: gunicorn app:app --bind 0.0.0.0:$PORT

# Worker process: Runs Celery to process queued tasks (e.g., audit_website)
worker: celery -A app.celery_app worker --loglevel=info

# Scheduler process: Runs Celery beat to schedule recurring tasks (e.g., daily_audit_all)
scheduler: celery -A app.celery_app beat --loglevel=info
