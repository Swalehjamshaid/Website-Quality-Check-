# Defines the main web application process (Gunicorn)
# 'app' is the module name (app.py), and the second 'app' is the object 
# returned by create_app() which is globally assigned to 'app' in app.py.
web: gunicorn app:app --bind 0.0.0.0:$PORT

# Defines the Celery worker process to handle audit_website tasks
# 'app.celery_app' is the Celery application instance in the app.py module.
worker: celery -A app.celery_app worker --loglevel=info

# Defines the Celery beat scheduler for recurring daily_audit_all tasks
scheduler: celery -A app.celery_app beat --loglevel=info
