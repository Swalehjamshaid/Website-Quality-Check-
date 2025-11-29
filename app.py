import os

class Config(object):
    """Base configuration class."""
    
    # Flask Security - MUST be set in Vercel Environment Variables
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-fallback-key'
    
    # Celery Configuration - MUST be set in Vercel Environment Variables
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # Supabase/API Configuration - MUST be set in Vercel Environment Variables
    SUPABASE_URL = os.environ.get('SUPABASE_URL') or 'http://mock-supabase.com'
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY') or 'mock-key'


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True


config_map = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
