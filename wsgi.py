# wsgi.py

# Assuming your application object is named 'app' in 'app.py'
from app import app as application

# The 'application' variable is now the callable that Gunicorn can use
# (If you kept 'web: gunicorn wsgi:application' in the Procfile)
