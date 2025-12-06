# Procfile

# Direct Gunicorn to the callable named 'app' inside the module 'app' (i.e., app.py)
web: gunicorn app:app

# Keep your Celery worker command if you use background tasks
celery: celery -A celery_worker app_worker --loglevel=info
