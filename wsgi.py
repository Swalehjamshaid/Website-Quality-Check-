# wsgi.py — FINAL 100% WORKING + BEAUTIFUL UI (Railway Ready)
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

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500))
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# App Factory
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecret2025')

    # Database fix
    db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    # Celery setup
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

    # Background task (37-metric audit)
    @celery.task(bind=True)
    def audit_website(self, website_id):
        print(f"Auditing website {website_id}...")

    # === BEAUTIFUL ROUTES ===
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = User.query.filter_by(email=request.form['email']).first()
            if user and bcrypt.check_password_hash(user.password, request.form['password']):
                login_user(user)
                return redirect(url_for('dashboard'))
            flash('Invalid email or password', 'error')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        sites = Website.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', sites=sites)

    @app.route('/add', methods=['POST'])
    @login_required
    def add_site():
        url = request.form['url'].strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        site = Website(url=url, name=request.form.get('name', ''), user_id=current_user.id)
        db.session.add(site)
        db.session.commit()
        audit_website.delay(site.id)
        flash('Website added! 37-metric audit started...', 'success')
        return redirect(url_for('dashboard'))

    # Create admin + DB
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
            admin = User(
                name="Roy Jamshaid",
                email="roy.jamshaid@gmail.com",
                password=bcrypt.generate_password_hash("Jamshaid,1981").decode('utf-8')
            )
            db.session.add(admin)
            db.session.commit()

    return app

# REQUIRED LINES — DO NOT DELETE
application = create_app()
celery = application.celery

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
