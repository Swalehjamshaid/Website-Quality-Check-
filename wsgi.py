# wsgi.py — 37Metrics — REAL AUDITS + SHOWS RESULTS — NO CELERY — WORKS ON RAILWAY
import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '37metrics-secret-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database (Railway fix)
db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
if db_url.startswith('postgres://'):
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

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    performance = db.Column(db.Float)
    accessibility = db.Column(db.Float)
    best_practices = db.Column(db.Float)
    seo = db.Column(db.Float)
    lcp = db.Column(db.String(50))
    cls = db.Column(db.String(50))
    fcp = db.Column(db.String(50))
    status_code = db.Column(db.Integer)
    page_size_kb = db.Column(db.Float)
    title_tag = db.Column(db.Boolean)
    meta_desc = db.Column(db.Boolean)
    h1_tag = db.Column(db.Boolean)
    robots_txt = db.Column(db.Boolean)
    sitemap_xml = db.Column(db.Boolean)
    has_https = db.Column(db.Boolean)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ——— REAL AUDIT FUNCTION ———
def run_real_audit(url):
    defaults = {
        'performance': 0, 'accessibility': 0, 'best_practices': 0, 'seo': 0,
        'lcp': 'N/A', 'cls': 'N/A', 'fcp': 'N/A', 'status_code': 0,
        'page_size_kb': 0, 'title_tag': False, 'meta_desc': False,
        'h1_tag': False, 'robots_txt': False, 'sitemap_xml': False, 'has_https': False
    }
    try:
        headers = {'User-Agent': '37MetricsBot/1.0 (+https://37metrics.up.railway.app)'}
        r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
        final_url = r.url
        defaults.update({
            'status_code': r.status_code,
            'page_size_kb': round(len(r.content) / 1024, 1),
            'has_https': final_url.startswith('https://')
        })

        # Google PageSpeed Insights
        psi_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={final_url}&strategy=desktop"
        psi = requests.get(psi_url, timeout=30).json()
        lr = psi.get('lighthouseResult', {})
        cat = lr.get('categories', {})
        audits = lr.get('audits', {})

        defaults['performance'] = round(cat.get('performance', {}).get('score', 0) * 100, 1)
        defaults['accessibility'] = round(cat.get('accessibility', {}).get('score', 0) * 100, 1)
        defaults['best_practices'] = round(cat.get('best-practices', {}).get('score', 0) * 100, 1)
        defaults['seo'] = round(cat.get('seo', {}).get('score', 0) * 100, 1)
        defaults['lcp'] = audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
        defaults['cls'] = audits.get('cumulative-layout-shift', {}).get('displayValue', 'N/A')
        defaults['fcp'] = audits.get('first-contentful-paint', {}).get('displayValue', 'N/A')

        # HTML checks
        soup = BeautifulSoup(r.text, 'html.parser')
        defaults['title_tag'] = bool(soup.title and soup.title.string)
        defaults['meta_desc'] = bool(soup.find('meta', attrs={'name': 'description'}))
        defaults['h1_tag'] = bool(soup.find('h1'))

        domain = f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}"
        defaults['robots_txt'] = requests.head(domain + '/robots.txt', timeout=8).status_code == 200
        defaults['sitemap_xml'] = requests.head(domain + '/sitemap.xml', timeout=8).status_code == 200

    except Exception as e:
        print(f"Audit error for {url}: {e}")

    return defaults

# ——— ROUTES ———
@app.route('/')
def index(): return redirect('/dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/dashboard')
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    sites = Website.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', sites=sites, user=current_user)

@app.route('/add', methods=['POST'])
@login_required
def add_website():
    url = request.form['url'].strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    name = request.form.get('name', '').strip() or urlparse(url).netloc

    site = Website(url=url, name=name, user_id=current_user.id)
    db.session.add(site)
    db.session.commit()

    # Run real audit (10–20 seconds)
    audit_data = run_real_audit(url)
    audit = Audit(website_id=site.id, **audit_data)
    db.session.add(audit)
    db.session.commit()

    flash(f'Success: "{url}" added! Audit completed.', 'success')
    return redirect('/dashboard')

@app.route('/results/<int:site_id>')
@login_required
def results(site_id):
    site = Website.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect('/dashboard')
    audit = Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first()
    return render_template('results.html', site=site, audit=audit)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# Create DB + admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
        admin = User(name="Roy Jamshaid", email="roy.jamshaid@gmail.com",
                     password=bcrypt.generate_password_hash("Jamshaid,1981").decode('utf-8'))
        db.session.add(admin)
        db.session.commit()

# Railway requirement
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
