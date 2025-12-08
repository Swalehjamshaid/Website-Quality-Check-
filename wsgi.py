# wsgi.py — FINAL WORKING VERSION — NO CRASH ON RAILWAY — Dec 2025
import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ffwebaudit-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database fix
db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

# Email (Set in Railway Variables)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'FF Web Audit <no-reply@ffwebaudit.com>'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Logo (safe fallback if file missing)
try:
    with open("ff_logo.png", "rb") as f:
        LOGO_BASE64 = base64.b64encode(f.read()).decode()
except:
    LOGO_BASE64 = ""  # Will show text logo

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500))
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

def get_grade(score):
    if score >= 90: return "A", "#28a745"
    elif score >= 80: return "B", "#74b816"
    elif score >= 70: return "C", "#ffc107"
    elif score >= 60: return "D", "#fd7e14"
    else: return "F", "#dc3545"

def run_audit(url):
    result = {"performance": 0, "accessibility": 0, "best_practices": 0, "seo": 0,
              "lcp": "N/A", "cls": "N/A", "fcp": "N/A", "status_code": 0, "page_size_kb": 0,
              "title_tag": False, "meta_desc": False, "robots_txt": False, "has_https": False}
    
    try:
        headers = {'User-Agent': 'FFWebAuditBot/1.0'}
        r = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
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

        result['grade'], result['color'] = get_grade(result['performance'])

    except Exception as e:
        print("Audit failed:", e)

    return result

@app.route('/')
def index(): return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/dashboard')
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already taken')
        else:
            user = User(name=request.form['name'], email=request.form['email'],
                        password=bcrypt.generate_password_hash(request.form['password']))
            db.session.add(user)
            db.session.commit()
            flash('Registered! Please login.')
            return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    sites = Website.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', sites=sites, logo=LOGO_BASE64)

@app.route('/add', methods=['POST'])
@login_required
def add():
    url = request.form['url'].strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    name = request.form.get('name', urlparse(url).netloc)
    
    site = Website(url=url, name=name, user_id=current_user.id)
    db.session.add(site)
    db.session.commit()

    data = run_audit(url)
    audit = Audit(website_id=site.id, data=json.dumps(data))
    db.session.add(audit)
    db.session.commit()

    flash('Website added & audit completed!')
    return redirect('/dashboard')

@app.route('/results/<int:site_id>')
@login_required
def results(site_id):
    site = Website.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        return redirect('/dashboard')
    audit = json.loads(Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first().data)
    return render_template('results.html', site=site, audit=audit, logo=LOGO_BASE64)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
