# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import requests, time, io, base64
from bs4 import BeautifulSoup
from weasyprint import HTML
from datetime import datetime
import matplotlib.pyplot as plt
from celery import Celery
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
celery_app = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery_app.conf.update(app.config)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models import User, Website, Audit

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()
    if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
        admin = User(
            email='roy.jamshaid@gmail.com',
            name='Roy Jamshaid',
            password=bcrypt.generate_password_hash('Jamshaid,1981').decode('utf-8'),
            is_admin=True,
            report_frequency='daily',
            report_time='09:00'
        )
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/'); def index(): return redirect(url_for('login')) if not current_user.is_authenticated else redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already exists', 'danger')
        else:
            user = User(email=request.form['email'], name=request.form['name'],
                        password=bcrypt.generate_password_hash(request.form['password']).decode('utf-8'))
            db.session.add(user)
            db.session.commit()
            flash('Registered! Login now', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    sites = Website.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', sites=sites)

@app.route('/add-website', methods=['GET', 'POST'])
@login_required
def add_website():
    if request.method == 'POST':
        url = request.form['url']
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        site = Website(url=url, name=request.form.get('name'), user_id=current_user.id)
        db.session.add(site)
        db.session.commit()
        audit_website.delay(site.id)
        flash('Website added & audit started!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_website.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.report_frequency = request.form['frequency']
        current_user.report_time = request.form['time']
        if current_user.report_frequency != 'daily':
            current_user.report_day = request.form['day']
        db.session.commit()
        flash('Schedule updated!', 'success')
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    return render_template('settings.html', days=days)

# More routes (generate_report, etc.) → I’ll give templates next

if __name__ == '__main__':
    app.run(debug=True)
