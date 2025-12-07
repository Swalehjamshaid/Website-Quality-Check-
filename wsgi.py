# wsgi.py — FINAL 100% WORKING VERSION (Railway Dec 2025)
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from celery import Celery

# Extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='User')
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))

# App Factory
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')

    # Database fix
    db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    # Celery
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    app.config['broker_url'] = redis_url
    app.config['result_backend'] = redis_url

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Celery
    def make_celery(app):
        celery = Celery(app.import_name, broker=app.config['broker_url'], backend=app.config['result_backend'])
        celery.conf.update(app.config)
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        celery.Task = ContextTask
        return celery

    celery = make_celery(app)
    app.celery = celery

    # Simple working route
    @app.route('/')
    def index():
        return '<h1 style="text-align:center;margin-top:100px">37Metrics is LIVE!</h1><p style="text-align:center"><a href="/login">Login</a></p>'

    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method == 'POST':
            user = User.query.filter_by(email=request.form['email']).first()
            if user and bcrypt.check_password_hash(user.password, request.form['password']):
                login_user(user)
                return redirect('/dashboard')
            flash('Wrong credentials')
        return '''
        <h2>Login</h2>
        <form method="post">
            Email: <input name="email" value="roy.jamshaid@gmail.com"><br><br>
            Password: <input name="password" type="password" value="Jamshaid,1981"><br><br>
            <button>Login</button>
        </form>
        '''

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return f'<h1>Welcome {current_user.name}! Your SaaS is LIVE!</h1>'

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect('/')

    # Create admin
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
            admin = User(name="Roy", email="roy.jamshaid@gmail.com",
                        password=bcrypt.generate_password_hash("Jamshaid,1981").decode('utf-8'))
            db.session.add(admin)
            db.session.commit()

    return app

# THESE TWO LINES MUST BE AFTER create_app() DEFINITION
application = create_app()
celery = application.celery

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
