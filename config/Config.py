# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv() 

class Config:
    """Base configuration settings for the application."""
    
    # --- Supabase/Database Configuration ---
    # The key provided is a SERVICE_ROLE key, which grants full permissions. 
    # Must be kept secret and only used on the backend.
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # --- Flask & Security ---
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-default-secret-key-for-local-use')
    
    # --- Celery Configuration (using Redis for broker/backend) ---
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Optional fallback settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///local_fallback.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
