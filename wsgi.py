# wsgi.py
from app import app

# This makes it work on Vercel
application = app

# Force install WeasyPrint dependencies (important for future PDF)
try:
    import weasyprint
    import cairo
except ImportError:
    pass
