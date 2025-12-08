# wsgi.py — FF Web Audit Pro — Complete with Scheduling, PDF, Graphs — Dec 2025
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
import matplotlib.pyplot as plt
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ffwebaudit-pro-2025')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database
db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

# Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
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

# Logo
try:
    with open("ff_logo.png", "rb") as f:
        LOGO_BASE64 = base64.b64encode(f.read()).decode()
except:
    LOGO_BASE64 = ""

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    frequency = db.Column(db.String(20), default='never')  # never, daily, weekly, monthly
    send_time = db.Column(db.String(5), default='09:00')   # HH:MM

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def generate_suggestions(audit):
    p = audit['performance']
    suggestions = []
    if p < 70: suggestions.append("Optimize images and enable lazy loading")
    if p < 80: suggestions.append("Minify CSS/JS and defer non-critical scripts")
    if not audit['title_tag']: suggestions.append("Add a unique <title> tag")
    if not audit['meta_desc']: suggestions.append("Add meta description for better SEO")
    if not audit['robots_txt']: suggestions.append("Create robots.txt file")
    return suggestions if suggestions else ["Excellent! Your site is highly optimized."]

def run_audit(url):
    result = {"performance":0,"accessibility":0,"best_practices":0,"seo":0,
              "lcp":"N/A","cls":"N/A","fcp":"N/A","status_code":0,"page_size_kb":0,
              "title_tag":False,"meta_desc":False,"robots_txt":False,"has_https":False}
    try:
        headers = {'User-Agent': 'FFWebAuditBot/1.0'}
        r = requests.get(url, timeout=25, headers=headers, allow_redirects=True)
        final_url = r.url
        result.update({"status_code":r.status_code,"page_size_kb":round(len(r.content)/1024,1),
                       "has_https":final_url.startswith('https://')})

        psi = requests.get(f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={final_url}&strategy=desktop", timeout=30).json()
        lr = psi.get('lighthouseResult', {})
        cat = lr.get('categories', {})
        audits = lr.get('audits', {})
        result['performance'] = round(cat.get('performance', {}).get('score', 0) * 100, 1)
        result['accessibility'] = round(cat.get('accessibility', {}).get('score', 0) * 100, 1)
        result['best_practices'] = round(cat.get('best-practices', {}).get('score', 0) * 100, 1)
        result['seo'] = round(cat.get('seo', {}).get('score', 0) * 100, 1)
        result['lcp'] = audits.get('largest-contentful-paint', {}).get('displayValue','N/A')
        result['cls'] = audits.get('cumulative-layout-shift', {}).get('displayValue','N/A')
        result['fcp'] = audits.get('first-contentful-paint', {}).get('displayValue','N/A')

        soup = BeautifulSoup(r.text, 'html.parser')
        result['title_tag'] = bool(soup.title and soup.title.string)
        result['meta_desc'] = bool(soup.find('meta', attrs={'name':'description'}))
        result['robots_txt'] = requests.head(f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/robots.txt", timeout=8).status_code == 200
    except Exception as e:
        print("Audit Error:", e)
    result['suggestions'] = generate_suggestions(result)
    result['grade'] = "A" if result['performance']>=90 else "B" if result['performance']>=80 else "C" if result['performance']>=70 else "D" if result['performance']>=60 else "F"
    return result

def get_history_graph(website_id):
    audits = Audit.query.filter_by(website_id=website_id).order_by(Audit.created_at).all()
    if len(audits) < 2: return ""
    dates = [a.created_at.strftime("%b %d") for a in audits]
    scores = [json.loads(a.data)['performance'] for a in audits]
    plt.figure(figsize=(8,4))
    plt.plot(dates, scores, marker='o', color='#5e35b1')
    plt.title("Performance Score Over Time")
    plt.ylim(0,100)
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def send_scheduled_reports():
    with app.app_context():
        now = datetime.now().strftime("%H:%M")
        sites = Website.query.filter(Website.frequency != 'never').all()
        for site in sites:
            if site.send_time == now[:5]:
                user = User.query.get(site.user_id)
                audit = run_audit(site.url)
                Audit(website_id=site.id, data=json.dumps(audit)).save()
                pdf = HTML(string=render_template('pdf_report.html', site=site, audit=audit, logo=LOGO_BASE64, graph=get_history_graph(site.id))).write_pdf()
                msg = Message(f"Your {site.frequency.title()} Website Audit Report", recipients=[user.email])
                msg.attach("FF_Web_Audit_Report.pdf", "application/pdf", pdf)
                mail.send(msg)

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_scheduled_reports, trigger="cron", minute="*", hour="*")
scheduler.start()

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/dashboard')
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already exists')
        else:
            user = User(name=request.form['name'], email=request.form['email'],
                        password=bcrypt.generate_password_hash(request.form['password']))
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully!')
            return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    sites = Website.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', sites=sites)

@app.route('/add', methods=['POST'])
@login_required
def add():
    url = request.form['url'].strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    site = Website(url=url, name=request.form.get('name',''), user_id=current_user.id,
                   frequency=request.form.get('frequency','never'), send_time=request.form.get('time','09:00'))
    db.session.add(site)
    db.session.commit()
    audit_data = run_audit(url)
    db.session.add(Audit(website_id=site.id, data=json.dumps(audit_data)))
    db.session.commit()
    flash('Website added & audit completed!', 'success')
    return redirect('/dashboard')

@app.route('/results/<int:site_id>')
@login_required
def results(site_id):
    site = Website.query.get_or_404(site_id)
    if site.user_id != current_user.id: return redirect('/dashboard')
    audit = json.loads(Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first().data)
    graph = get_history_graph(site_id)
    return render_template('results.html', site=site, audit=audit, graph=graph)

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
