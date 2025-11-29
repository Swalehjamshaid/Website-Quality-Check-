# config.py
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-fallback-key")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # Add this in Vercel env vars
    
    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

    # Folders
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    REPORTS_FOLDER = os.path.join(BASE_DIR, "static", "reports")

# Ensure reports folder exists
if not os.path.exists(Config.REPORTS_FOLDER):
    os.makedirs(Config.REPORTS_FOLDER)

config_map = {
    "development": Config,
    "production": Config,
    "default": Config,
}
