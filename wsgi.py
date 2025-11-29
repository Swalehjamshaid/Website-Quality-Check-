# wsgi.py

from app import app as application

# 'application' is the standard name that Vercel and Gunicorn look for 
# when starting a Python web server using the WSGI specification.
