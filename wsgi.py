# wsgi.py

# Import the application factory function from your main application file
from app import create_app

# Create the application object instance using the factory function
application = create_app()
