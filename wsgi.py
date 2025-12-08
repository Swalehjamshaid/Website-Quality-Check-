# wsgi.py - FF Web Audit - Professional 37Metrics SaaS - Dec 2025
import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from weasyprint import HTML
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ffwebaudit-super-secret-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database
db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

# Email Config (Use Gmail or Brevo/SendGrid)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('FF Web Audit', 'no-reply@ffwebaudit.com')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Load Logo
with open("ff_logo.png", "rb") as f:
    LOGO_BASE64 = base64.b64encode(f.read()).decode()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    schedule = db.Column(db.String(20), default='never')  # never, daily, weekly

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.Text)  # JSON string of all results

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def get_grade(score):
    if score >= 90: return "A", "#28a745"
    elif score >= 80: return "B", "#74b816"
    elif score >= 70: return "C", "#ffc107"
    elif score >= 60: return "D", "#fd7e14"
    else: return "F", "#dc3545"

def run_37metrics_audit(url):
    result = {
        "performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0,
        "lcp": "N/A", "cls": "N/A", "fcp": "N/A", "status_code": 0,
        "page_size_kb": 0, "has_https": False, "title_tag": False,
        "meta_desc": False, "h1_tag": False, "robots_txt": False,
        "sitemap_xml": False, "alt_tags_percent": 0, "broken_links": 0
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

        # PageSpeed Insights
        psi = requests.get(f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={final_url}&strategy=desktop").json()
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
        result['h1_tag'] = bool(soup.find('h1'))
        result['alt_tags_percent'] = round((len([img for img in soup.find_all('img') if img.get('alt')]) / max(1, len(soup.find_all('img')))) * 100, 1)

        domain = f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}"
        result['robots_txt'] = requests.head(domain + '/robots.txt', timeout=8).status_code == 200
        result['sitemap_xml'] = requests.head(domain + '/sitemap.xml', timeout=8).status_code == 200

    except Exception as e:
        print("Audit Error:", e)

    result['overall_grade'], result['grade_color'] = get_grade(result['performance'])
    return result

def send_scheduled_emails():
    with app.app_context():
        for site in Website.query.filter(Website.schedule != 'never').all():
            user = User.query.get(site.user_id)
            audit_data = run_37metrics_audit(site.url)
            pdf = HTML(string=render_template('pdf_report.html', site=site, audit=audit_data, logo=LOGO_BASE64)).write_pdf()

            msg = Message("Your FF Web Audit Report", recipients=[user.email])
            msg.body = f"Hi {user.name},\n\nHere's your scheduled website audit report for {site.name or site.url}."
            msg.attach("FF_Web_Audit_Report.pdf", "application/pdf", pdf)
            mail.send(msg)

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_scheduled_emails, trigger="cron", hour=8)  # Daily at 8 AM
scheduler.start()

@app.route('/')
def index(): return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        user = User(name=request.form['name'], email=request.form['email'],
                    password=bcrypt.generate_password_hash(request.form['password']))
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    sites = Website.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', sites=sites)

@app.route('/add', methods=['POST'])
@login_required
def add_website():
    url = request.form['url'].strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    site = Website(url=url, name=request.form.get('name', ''), user_id=current_user.id,
                   schedule=request.form.get('schedule', 'never'))
    db.session.add(site)
    db.session.commit()

    audit_data = run_37metrics_audit(url)
    audit = Audit(website_id=site.id, data=json.dumps(audit_data))
    db.session.add(audit)
    db.session.commit()

    flash('Website added & audit completed!')
    return redirect(url_for('dashboard'))

@app.route('/results/<int:site_id>')
@login_required
def results(site_id):
    site = Website.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('dashboard'))
    audit = json.loads(Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first().data)
    return render_template('results.html', site=site, audit=audit, logo=LOGO_BASE64)

@app.route('/download/<int:site_id>')
@login_required
def download(site_id):
    site = Website.query.get_or_404(site_id)
    audit = json.loads(Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first().data)
    pdf = HTML(string=render_template('pdf_report.html', site=site, audit=audit, logo=LOGO_BASE64)).write_pdf()
    return send_file(pdf, as_attachment=True, download_name=f"FF_Audit_{site.name}.pdf")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
        admin = User(name="Roy Jamshaid", email="roy.jamshaid@gmail.com",
                     password=bcrypt.generate_password_hash("Jamshaid,1981"), is_admin=True)
        db.session.add(admin)
        db.session.commit()

application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
