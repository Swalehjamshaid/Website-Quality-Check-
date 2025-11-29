# wsgi.py

from app import create_app
import os

# Call the factory function to create the application instance
application = create_app(config_name=os.environ.get('FLASK_CONFIG', 'default'))
