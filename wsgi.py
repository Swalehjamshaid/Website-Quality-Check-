# wsgi.py

from app import create_app

# Call the factory function to create the application instance
application = create_app(config_name=os.environ.get('FLASK_CONFIG', 'default'))

# 'application' is now the callable Flask object that Vercel needs.
