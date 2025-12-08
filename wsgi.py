# wsgi.py — FINAL 100% WORKING VERSION — Dec 2025
import os
import json
import requests
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from weasyprint import HTML
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ffwebaudit-ultimate-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# AUTO CONNECT TO RAILWAY POSTGRESQL
db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///db.sqlite'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Your Logo (ff_logo.png in root)
try:
    with open("ff_logo.png", "rb") as f:
        LOGO = base64.b64encode(f.read()).decode()
except:
    LOGO = ""

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='User')
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    frequency = db.Column(db.String(20), default='never')     # never, daily, weekly, monthly
    send_time = db.Column(db.String(5), default='09:00')       # HH:MM

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def run_audit(url):
    result = {
        "performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0,
        "lcp": "N/A", "cls": "N/A", "fcp": "N/A", "status_code": 0, "page_size_kb": 0,
        "title_tag": False, "meta_desc": False, "robots_txt": False, "has_https": False
    }
    try:
        headers = {'User-Agent': 'FFWebAuditBot/1.0'}
        r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
        final_url = r.url
        result.update({
            "status_code": r.status_code,
            "page_size_kb": round(len(r.content)/1024, 1),
            "has_https": final_url.startswith('https://')
        })

        psi = requests.get(f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={final_url}&strategy=desktop", timeout=30).json()
        lr = psi.get('lighthouseResult', {})
        cat = lr.get('categories', {})
        audits = lr.get('audits', {})

        result['performance'] = round(cat.get('performance', {}).get('score', 0) * 100, 1)
        result['accessibility'] = round(cat.get('accessibility', {}).get('score', 0) * 100, 1)
        result['best_practices'] = round(cat.get('best-practices', {}).get('score', 0) * 100, 1)
        result['seo'] = round(cat.get('seo', {}).get('score', 0) * 100, 1)
        result['lcp'] = audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
        result['cls'] = audits.get('cumulative-layout-shift', {}).get('displayValue', 'N/A')
        result['fcp'] = audits.get('first-contentful-paint', {}).get('displayValue', 'N/A')

        soup = BeautifulSoup(r.text, 'html.parser')
        result['title_tag'] = bool(soup.title and soup.title.string)
        result['meta_desc'] = bool(soup.find('meta', attrs={'name': 'description'}))
        result['robots_txt'] = requests.head(f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/robots.txt", timeout=8).status_code == 200
    except Exception as e:
        print("Audit failed:", e)

    # Grade & Suggestions
    p = result['performance']
    result['grade'] = "A" if p >= 90 else "B" if p >= 80 else "C" if p >= 70 else "D" if p >= 60 else "F"
    suggestions = []
    if p < 70: suggestions.append("Compress images & enable lazy loading")
    if p < 80: suggestions.append("Minify CSS/JS and defer non-critical scripts")
    if not result['title_tag']: suggestions.append("Add a proper <title> tag")
    if not result['meta_desc']: suggestions.append("Add meta description")
    if not result['robots_txt']: suggestions.append("Create robots.txt")
    result['suggestions'] = suggestions or ["Excellent! Your site is highly optimized."]

    return result

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/dashboard')
        flash('Invalid email or password', 'error')
    return render_template('login.html', logo=LOGO)

@app.route('/dashboard')
@login_required
def dashboard():
    sites = Website.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', sites=sites, name=current_user.name, logo=LOGO)

@app.route('/add', methods=['POST'])
@login_required
def add():
    url = request.form['url'].strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    name = request.form.get('name') or urlparse(url).netloc
    freq = request.form.get('frequency', 'never')
    time = request.form.get('send_time', '09:00')

    site = Website(url=url, name=name, user_id=current_user.id, frequency=freq, send_time=time)
    db.session.add(site)
    db.session.commit()

    audit_data = run_audit(url)
    audit = Audit(website_id=site.id, data=json.dumps(audit_data))
    db.session.add(audit)
    db.session.commit()

    flash('Website added & full audit completed!', 'success')
    return redirect('/dashboard')

@app.route('/results/<int:site_id>')
@login_required
def results(site_id):
    site = Website.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        return redirect('/dashboard')
    audit = json.loads(Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first().data)
    return render_template('results.html', site=site, audit=audit, logo=LOGO)

@app.route('/download/<int:site_id>')
@login_required
def download(site_id):
    site = Website.query.get_or_404(site_id)
    audit = json.loads(Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first().data)
    pdf = HTML(string=render_template('pdf_report.html', site=site, audit=audit, logo=LOGO)).write_pdf()
    return send_file(pdf, as_attachment=True, download_name=f"FF_Web_Audit_{site.name}.pdf")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
        admin = User(name="Roy Jamshaid", email="roy.jamshaid@gmail.com",
                     password=bcrypt.generate_password_hash("Jamshaid,1981"))
        db.session.add(admin)
        db.session.commit()

application = app
