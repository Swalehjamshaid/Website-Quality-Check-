# wsgi.py — 100% Python-only, production-ready async audits
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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

# ==================== CORE SETUP ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '37metrics-pro-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database
db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///db.sqlite'

# Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ThreadPool for background audits
executor = ThreadPoolExecutor(max_workers=10)  # Handles multiple audits concurrently

PAGESPEED_API_KEY = os.getenv('PAGESPEED_API_KEY')

# Logo
try:
    with open("ff_logo.png", "rb") as f:
        LOGO = base64.b64encode(f.read()).decode()
except:
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

# ==================== BACKGROUND AUDIT ====================
def run_full_audit_task(website_id):
    """Background audit task."""
    with app.app_context():
        site = Website.query.get(website_id)
        if not site:
            print(f"Website ID {website_id} not found.")
            return

        url = site.url
        result = {
            "performance":0,"accessibility":0,"best_practices":0,"seo":0,"pwa":0,
            "lcp":"N/A","cls":"N/A","fcp":"N/A","tbt":"N/A","tti":"N/A","speed_index":"N/A",
            "page_size_kb":0,"total_requests":0,"has_https":False,
            "server_response_time":"N/A","title_tag":False,"meta_description":False,
            "robots_txt":False,"sitemap_xml":False,"gzip_compression":False,
            "grade":"F","overall_score":0
        }

        try:
            headers = {'User-Agent': '37Metrics-Pro-Auditor v2.0 (+https://37metrics.live)'}
            r = requests.get(url, timeout=30, headers=headers, allow_redirects=True)
            final_url = r.url
            soup = BeautifulSoup(r.text, 'html.parser')

            result.update({
                "page_size_kb": round(len(r.content)/1024,1),
                "server_response_time": f"{r.elapsed.total_seconds():.2f}s",
                "has_https": final_url.startswith('https://'),
                "title_tag": bool(soup.title and soup.title.string and len(soup.title.string.strip())>0),
                "meta_description": bool(soup.find('meta', attrs={'name':'description'})),
                "robots_txt": requests.head(f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/robots.txt", timeout=8).status_code==200,
                "sitemap_xml": requests.head(f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/sitemap.xml", timeout=8).status_code==200,
                "gzip_compression": 'gzip' in r.headers.get('content-encoding','').lower() or 'br' in r.headers.get('content-encoding','').lower()
            })

            if PAGESPEED_API_KEY:
                pagespeed_api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
                params = {"url": final_url,"strategy":"desktop","category":["performance","accessibility","best-practices","seo","pwa"],"key":PAGESPEED_API_KEY}
                psi_res = requests.get(pagespeed_api_url, params=params, timeout=60)
                if psi_res.status_code==200:
                    psi = psi_res.json()
                    lr = psi.get('lighthouseResult', {})
                    cat = lr.get('categories', {})
                    audits = lr.get('audits', {})
                    result['performance'] = round(cat.get('performance', {}).get('score',0)*100,1)
                    result['accessibility'] = round(cat.get('accessibility', {}).get('score',0)*100,1)
                    result['best_practices'] = round(cat.get('best-practices', {}).get('score',0)*100,1)
                    result['seo'] = round(cat.get('seo', {}).get('score',0)*100,1)
                    result['lcp'] = audits.get('largest-contentful-paint', {}).get('displayValue','N/A')
                    result['cls'] = audits.get('cumulative-layout-shift', {}).get('displayValue','N/A')
                    result['fcp'] = audits.get('first-contentful-paint', {}).get('displayValue','N/A')
        except Exception as e:
            print(f"37Metrics Audit Error for {url}: {e}")

        # Calculate grade
        avg = (result['performance']+result['accessibility']+result['best_practices']+result['seo'])/4
        result['overall_score'] = round(avg,1)
        result['grade'] = "A" if avg>=90 else "B" if avg>=80 else "C" if avg>=70 else "D" if avg>=60 else "F"

        # Save audit
        try:
            audit = Audit(website_id=website_id, data=json.dumps(result))
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"DB Error saving audit: {e}")

        print(f"Audit for {url} completed with score {result['overall_score']}")

# ==================== ROUTES ====================
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
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
    return render_template('dashboard.html', sites=sites, name=current_user.name or "User", logo=LOGO)

@app.route('/add', methods=['POST'])
@login_required
def add():
    url = request.form['url'].strip()
    if not url.startswith(('http://','https://')):
        url = 'https://' + url
    name = request.form.get('name', urlparse(url).netloc)

    site = Website(url=url, name=name, user_id=current_user.id)
    try:
        db.session.add(site)
        db.session.commit()
        # Submit audit to thread pool (non-blocking)
        executor.submit(run_full_audit_task, site.id)
        flash('Audit started in background!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error starting audit: {e}", 'error')
    return redirect('/dashboard')

@app.route('/results/<int:site_id>')
@login_required
def results(site_id):
    site = Website.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        return redirect('/dashboard')
    latest = Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first()
    if not latest:
        audit = {"overall_score": "...", "performance": "...", "accessibility": "...", "seo": "...", "lcp": "N/A"}
        flash('Audit is still running in background.', 'warning')
    else:
        audit = json.loads(latest.data)
    return render_template('results.html', site=site, audit=audit, logo=LOGO)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# ==================== DB INIT ====================
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

# ==================== RUN ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
