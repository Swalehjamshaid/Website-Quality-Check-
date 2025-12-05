import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import requests, time, io, base64
from bs4 import BeautifulSoup
from weasyprint import HTML
import matplotlib
matplotlib.use('Agg')  # Non-interactive for Render
import matplotlib.pyplot as plt
# --- CRITICAL NEW IMPORTS ---
from celery import Celery
# Note: smtplib/email imports are omitted here but assumed to be in the final, complete app.
# ----------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '37metrics-secret-2025')

# CRITICAL FIX 1: Change DB path to /var/data/ to use the Persistent Disk defined in render.yaml
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:////var/data/monitor.db')  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CRITICAL FIX 2: Celery Configuration from Environment Variables
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

celery_app = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery_app.conf.update(app.config)
# ----------------------------------------------------------------------


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models (Full 37 Metrics - remain identical)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    report_frequency = db.Column(db.String(20), default='weekly')
    report_time = db.Column(db.String(5), default='09:00')
    report_day = db.Column(db.String(10))

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    load_time = db.Column(db.Float)
    page_size_kb = db.Column(db.Float)
    status_code = db.Column(db.Integer)
    lcp = db.Column(db.Float)
    fid = db.Column(db.Float)
    cls = db.Column(db.Float)
    fcp = db.Column(db.Float)
    tbt = db.Column(db.Float)
    seo_score = db.Column(db.Float)
    performance_score = db.Column(db.Float)
    accessibility_score = db.Column(db.Float)
    best_practices_score = db.Column(db.Float)
    mobile_responsive = db.Column(db.Boolean)
    has_https = db.Column(db.Boolean)
    robots_txt = db.Column(db.Boolean)
    sitemap_xml = db.Column(db.Boolean)
    canonical_tag = db.Column(db.Boolean)
    meta_description = db.Column(db.Boolean)
    title_tag = db.Column(db.Boolean)
    h1_tag = db.Column(db.Boolean)
    alt_tags = db.Column(db.Float)
    broken_links = db.Column(db.Integer)
    internal_links = db.Column(db.Integer)
    external_links = db.Column(db.Integer)
    compression_enabled = db.Column(db.Boolean)
    cache_policy = db.Column(db.Boolean)
    minified_css = db.Column(db.Boolean)
    minified_js = db.Column(db.Boolean)
    unused_css = db.Column(db.Float)
    unused_js = db.Column(db.Float)
    render_blocking = db.Column(db.Integer)
    third_party_requests = db.Column(db.Integer)
    server_response_time = db.Column(db.Float)
    ssl_valid = db.Column(db.Boolean)
    security_headers = db.Column(db.Integer)
    cookie_compliance = db.Column(db.Boolean)
    core_web_vitals_pass = db.Column(db.Boolean)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Init DB
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
        admin = User(name="Roy Jamshaid", email="roy.jamshaid@gmail.com",
                     password=bcrypt.generate_password_hash("Jamshaid,1981").decode('utf-8'), is_admin=True)
        db.session.add(admin)
        db.session.commit()


# --- CRITICAL FIX 3: Convert Audit Functions to Celery Tasks ---

@celery_app.task(bind=True)
def audit_website(self, wid):
    # This runs in the Render Worker Service (non-blocking)
    with app.app_context():
        site = Website.query.get(wid)
        if not site: return
        try:
            # --- Audit Logic (Identical to your original code) ---
            headers = {'User-Agent': '37MetricsBot/2025'}
            start = time.time()
            r = requests.get(site.url, timeout=20, headers=headers, allow_redirects=True)
            load_time = time.time() - start
            soup = BeautifulSoup(r.text, 'html.parser')
            imgs = soup.find_all('img')
            links = soup.find_all('a', href=True)

            audit = Audit(
                website_id=site.id,
                load_time=round(load_time, 2),
                page_size_kb=round(len(r.content)/1024, 1),
                status_code=r.status_code,
                lcp=round(load_time*1.7, 2), fid=45, cls=0.04, fcp=round(load_time*0.9, 2), tbt=200,
                seo_score=95 if soup.title else 40, performance_score=90, accessibility_score=94, best_practices_score=92,
                mobile_responsive=bool(soup.find('meta', {'name': 'viewport'})),
                has_https=site.url.startswith('https'), robots_txt=True, sitemap_xml=True,
                canonical_tag=bool(soup.find('link', rel='canonical')),
                meta_description=bool(soup.find('meta', name='description')),
                title_tag=bool(soup.title), h1_tag=bool(soup.find('h1')),
                alt_tags=round((len([i for i in imgs if i.get('alt')]) / max(1, len(imgs))) * 100, 1),
                broken_links=0, internal_links=len(links)//2, external_links=len(links)//2,
                compression_enabled='gzip' in r.headers.get('Content-Encoding', ''), cache_policy=bool(r.headers.get('Cache-Control')),
                minified_css=True, minified_js=True, unused_css=18.5, unused_js=42.3, render_blocking=10, third_party_requests=15,
                server_response_time=round(load_time*0.3, 2), ssl_valid=site.url.startswith('https'),
                security_headers=6, cookie_compliance=True, core_web_vitals_pass=load_time < 3.0
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            print(f"Audit failed: {e}")
            # Ensure a record is still created even if the audit fails
            db.session.add(Audit(website_id=site.id, load_time=0.0, page_size_kb=0.0, status_code=0))
            db.session.commit()

@celery_app.task(bind=True)
def daily_audit_all(self):
    # This task is triggered by the Render Beat Service daily
    with app.app_context():
        for website in Website.query.all():
            audit_website.delay(website.id) # Queues individual audit to the worker

@celery_app.task(bind=True)
def send_scheduled_reports(self):
    # This task is triggered by the Render Beat Service every 5 minutes (to check schedule)
    with app.app_context():
        # (Your scheduled report logic goes here)
        print("Running scheduled report checker...")


# --- Routes (Updated to use Celery) ---

@app.route('/'); def index(): return redirect(url_for('login'))
@app.route('/login', methods=['GET', 'POST']); # Login logic...
@app.route('/register', methods=['GET', 'POST']); # Registration logic...
@app.route('/logout'); # Logout logic...
@app.route('/dashboard'); # Dashboard logic...

@app.route('/add-website', methods=['GET', 'POST'])
@login_required
def add_website():
    if request.method == 'POST':
        url = request.form['url'].strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        site = Website(url=url, name=request.form.get('name'), user_id=current_user.id)
        db.session.add(site)
        db.session.commit()
        
        # CRITICAL FIX 4: Use .delay() to send the task to the Celery Worker, making the route non-blocking
        audit_website.delay(site.id)

        flash('Website added! Audit started in background.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_website.html')

@app.route('/site/<int:wid>'); # Site detail logic...
@app.route('/report/<int:wid>'); # Generate report logic...

# The if __name__ == '__main__' block is ignored by Gunicorn on Render.
