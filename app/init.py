import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from celery import Celery

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def make_celery(app: Flask):
    celery = Celery(
        app.import_name,
        broker=app.config.get("CELERY_BROKER_URL"),
        backend=app.config.get("CELERY_RESULT_BACKEND"),
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def create_app(config_object=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "37metrics-pro-2025")
    # Database URL: fix common HEROKU/RAILWAY prefix
    db_url = os.getenv("DATABASE_URL", "sqlite:///db.sqlite")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Celery/Redis
    app.config["CELERY_BROKER_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    app.config["CELERY_RESULT_BACKEND"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Register extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Blueprints / routes
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
