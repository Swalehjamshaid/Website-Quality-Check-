# wsgi.py
from app import app

# This single line is enough for Vercel + Gunicorn + Flask
application = app

# Optional: Force Vercel to install all dependencies (important for WeasyPrint!)
try:
    import weasyprint
    import cairo
    import gi
except ImportError:
    pass
