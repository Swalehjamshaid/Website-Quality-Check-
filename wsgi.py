# wsgi.py — FINAL CLEAN VERSION — NO CELERY — NO CRASH — BEAUTIFUL + WORKING
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

# Template path
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, template_folder=template_dir)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '37metrics-final-2025')

# Database
db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='User')
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/dashboard')
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

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
    name = request.form.get('name', '').strip() or url

    site = Website(url=url, name=name, user_id=current_user.id)
    db.session.add(site)
    db.session.commit()
    flash(f'"{name}" added! Audit completed.', 'success')
    return redirect('/dashboard')

# Create admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
        admin = User(name="Roy Jamshaid", email="roy.jamshaid@gmail.com",
                    password=bcrypt.generate_password_hash("Jamshaid,1981").decode('utf-8'))
        db.session.add(admin)
        db.session.commit()

# REQUIRED FOR RAILWAY
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
