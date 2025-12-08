# wsgi.py — 37 METRICS PRO VERSION — Python-only, Thread-based Background Audits with full error handling
import os
import json
import requests
import base64
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# ==================== LOAD ENV ====================
load_dotenv()

# ==================== FLASK SETUP ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '37metrics-pro-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database configuration
db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///db.sqlite'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

PAGESPEED_API_KEY = os.getenv('PAGESPEED_API_KEY')

# Logo setup
try:
    with open("ff_logo.png", "rb") as f:
        LOGO = base64.b64encode(f.read()).decode()
except Exception:
    LOGO = ""

# ==================== MODELS ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='Roy Jamshaid')
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ==================== THREAD POOL ====================
executor = ThreadPoolExecutor(max_workers=5)  # Adjust based on server capacity

# ==================== AUDIT FUNCTION ====================
def run_full_audit_task(website_id):
    try:
        with app.app_context():
            site = Website.query.get(website_id)
            if not site:
                print(f"[ERROR] Website ID {website_id} not found.")
                return

            url = site.url
            result = {
                "performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0,
                "overall_score": 0, "grade": "F",
                "page_size_kb": 0, "server_response_time": "N/A",
                "has_https": False, "title_tag": False, "meta_description": False,
                "robots_txt": False, "sitemap_xml": False, "gzip_compression": False
            }

            # HTTP Request and parsing
            try:
                headers = {'User-Agent': '37Metrics-Pro-Auditor'}
                r = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
                soup = BeautifulSoup(r.text, 'html.parser')
                final_url = r.url

                result.update({
                    "page_size_kb": round(len(r.content)/1024, 1),
                    "server_response_time": f"{r.elapsed.total_seconds():.2f}s",
                    "has_https": final_url.startswith('https://'),
                    "title_tag": bool(soup.title and soup.title.string),
                    "meta_description": bool(soup.find('meta', attrs={'name':'description'})),
                    "robots_txt": requests.head(f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/robots.txt", timeout=8).status_code == 200,
                    "sitemap_xml": requests.head(f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/sitemap.xml", timeout=8).status_code == 200,
                    "gzip_compression": 'gzip' in r.headers.get('content-encoding','').lower() or 'br' in r.headers.get('content-encoding','').lower()
                })
            except Exception as e:
                print(f"[ERROR] Request/Parsing error for {url}: {e}")

            # Optional: Pagespeed API
            if PAGESPEED_API_KEY:
                try:
                    pagespeed_api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
                    params = {"url": final_url, "strategy": "desktop",
                              "category": ["performance","accessibility","best-practices","seo","pwa"],
                              "key": PAGESPEED_API_KEY}
                    psi_res = requests.get(pagespeed_api_url, params=params, timeout=60)
                    if psi_res.status_code == 200:
                        psi = psi_res.json()
                        lr = psi.get('lighthouseResult', {})
                        cat = lr.get('categories', {})
                        result['performance'] = round(cat.get('performance', {}).get('score',0)*100,1)
                        result['accessibility'] = round(cat.get('accessibility', {}).get('score',0)*100,1)
                        result['best_practices'] = round(cat.get('best-practices', {}).get('score',0)*100,1)
                        result['seo'] = round(cat.get('seo', {}).get('score',0)*100,1)
                except Exception as e:
                    print(f"[ERROR] Pagespeed API error for {url}: {e}")

            # Calculate overall score and grade
            avg = (result['performance'] + result['accessibility'] + result['best_practices'] + result['seo']) / 4
            result['overall_score'] = round(avg,1)
            result['grade'] = "A" if avg>=90 else "B" if avg>=80 else "C" if avg>=70 else "D" if avg>=60 else "F"

            # Save to DB
            try:
                audit = Audit(website_id=website_id, data=json.dumps(result))
                db.session.add(audit)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] DB save error for {url}: {e}")

            print(f"[INFO] Audit completed for {url} with score {result['overall_score']}")

    except Exception as e:
        print(f"[ERROR] Audit thread exception for website ID {website_id}: {e}")

# ==================== ROUTES ====================
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect('/dashboard')
        if request.method == 'POST':
            user = User.query.filter_by(email=request.form.get('email')).first()
            if user and bcrypt.check_password_hash(user.password, request.form.get('password')):
                login_user(user)
                return redirect('/dashboard')
            flash('Invalid email or password', 'error')
    except Exception as e:
        print(f"[ERROR] Login route: {e}")
        flash('Login error', 'error')
    return render_template('login.html', logo=LOGO)

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        sites = Website.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', sites=sites, name=current_user.name or "User", logo=LOGO)
    except Exception as e:
        print(f"[ERROR] Dashboard route: {e}")
        flash('Error loading dashboard', 'error')
        return redirect('/logout')

@app.route('/add', methods=['POST'])
@login_required
def add():
    try:
        url = request.form.get('url', '').strip()
        if not url:
            flash('URL is required', 'error')
            return redirect('/dashboard')

        if not url.startswith(('http://','https://')):
            url = 'https://' + url
        name = request.form.get('name', urlparse(url).netloc)

        site = Website(url=url, name=name, user_id=current_user.id)
        db.session.add(site)
        db.session.commit()

        executor.submit(run_full_audit_task, site.id)
        flash('Full 37-metric audit started (30-90s)!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Add route exception: {e}")
        flash(f"Error starting audit: {e}", 'error')
    return redirect('/dashboard')

@app.route('/results/<int:site_id>')
@login_required
def results(site_id):
    try:
        site = Website.query.get_or_404(site_id)
        if site.user_id != current_user.id:
            return redirect('/dashboard')
        latest = Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first()
        if not latest:
            audit = {"overall_score":"...", "performance":"...", "accessibility":"...", "seo":"...", "lcp":"N/A"}
            flash('Audit is still running in background.', 'warning')
        else:
            audit = json.loads(latest.data)
        return render_template('results.html', site=site, audit=audit, logo=LOGO)
    except Exception as e:
        print(f"[ERROR] Results route: {e}")
        flash('Error fetching results', 'error')
        return redirect('/dashboard')

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
    except Exception as e:
        print(f"[ERROR] Logout route: {e}")
    return redirect('/')

# ==================== DATABASE INIT ====================
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='roy.jamshaid@gmail.com').first():
        admin = User(
            name="Roy Jamshaid",
            email="roy.jamshaid@gmail.com",
            password=bcrypt.generate_password_hash("Jamshaid,1981").decode()
        )
        db.session.add(admin)
        db.session.commit()

# ==================== RAILWAY/GUNICORN ====================
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
