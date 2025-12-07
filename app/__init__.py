# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-2025')
    
    # Database – Railway gives DATABASE_URL (PostgreSQL)
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///dev.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Celery + Redis (Railway Redis plugin)
    redis_url = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config.update(
        broker_url=redis_url,
        result_backend=redis_url,
        task_ignore_result=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
    )

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints/routes
    from .routes import bp
    app.register_blueprint(bp)

    # Create tables + admin user
    @app.before_first_request
    def create_tables():
        db.create_all()
        if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
            admin = User(
                name="Roy Jamshaid",
                email="roy.jamshaid@gmail.com",
                password=bcrypt.generate_password_hash(os.getenv('ADMIN_PASSWORD', 'Jamshaid,1981')).decode('utf-8'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

    return app
