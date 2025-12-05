# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import requests, time, io, base64
from bs4 import BeautifulSoup
from weasyprint import HTML
import matplotlib.pyplot as plt
from celery import Celery
from celery.schedules import crontab
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from urllib.parse import urljoin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Celery Configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
celery_app = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery_app.conf.update(app.config)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import models after db initialization
from models import User, Website, Audit

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()
    # Create default admin
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

# --- Routes ---

@app.route('/'); def index(): return redirect(url_for('login')) if not current_user.is_authenticated else redirect(url_for('dashboard'))
@app.route('/login', methods=['GET', 'POST']); # Login logic...
@app.route('/register', methods=['GET', 'POST']); # Registration logic...

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
        # Trigger audit immediately in the background
        audit_website_wrapper.delay(site.id) 
        flash('Website added & audit started!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_website.html')

@app.route('/website/<int:wid>')
@login_required
def website_detail(wid):
    website = Website.query.filter_by(id=wid, user_id=current_user.id).first_or_404()
    audits = Audit.query.filter_by(website_id=wid).order_by(Audit.timestamp.desc()).all()
    return render_template('website_detail.html', website=website, audits=audits)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.report_frequency = request.form['frequency']
        current_user.report_time = request.form['time']
        if current_user.report_frequency in ['weekly', 'monthly']:
            current_user.report_day = request.form['day']
        db.session.commit()
        flash('Schedule updated!', 'success')
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    return render_template('settings.html', days=days)

@app.route('/generate-report/<int:wid>')
@login_required
def generate_report(wid):
    website = Website.query.filter_by(id=wid, user_id=current_user.id).first_or_404()
    audits = Audit.query.filter_by(website_id=wid).order_by(Audit.timestamp).all()
    
    # Generate trend graph (Load Time) for PDF embedding
    fig, ax = plt.subplots(figsize=(6, 2))
    dates = [a.timestamp for a in audits]
    loads = [a.load_time for a in audits]
    ax.plot(dates, loads)
    ax.set_title('Load Time Trend (s)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Load Time (s)')
    ax.tick_params(axis='x', rotation=45, labelsize=8)
    plt.tight_layout()

    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png')
    plt.close(fig) 
    img_buffer.seek(0)
    plot_url = base64.b64encode(img_buffer.read()).decode()
    
    html = render_template('report_template.html', website=website, audits=audits, user=current_user, plot_url=plot_url)
    pdf = HTML(string=html, base_url=request.base_url).write_pdf()
    
    filename = f"Full_37Metrics_Report_{website.name or 'site'}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(io.BytesIO(pdf), as_attachment=True, download_name=filename, mimetype='application/pdf')

# --- Celery Tasks (The actual logic functions) ---

def audit_website(website_id):
    # This function contains the detailed 37-metric auditing logic (simplified simulation)
    website = Website.query.get(website_id)
    if not website: return
    # ... [Actual auditing logic for 37 metrics would go here, fetching data, parsing, simulating scores] ...
    # Simplified simulation:
    try:
        start_time = time.time()
        response = requests.get(website.url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        load_time = time.time() - start_time
        soup = BeautifulSoup(response.content, 'html.parser')

        # Dummy/Simulated Metrics:
        simulated_audit = Audit(
            website_id=website.id,
            load_time=round(load_time, 2),
            page_size_kb=round(len(response.content) / 1024, 2),
            status_code=response.status_code,
            lcp=round(load_time * 0.7, 2), # Example calculation
            seo_score=85.0 if soup.find('title') else 50.0,
            broken_links=len(soup.find_all('a', href=True)) % 5, # Simulate some broken links
            has_https=website.url.startswith('https'),
            mobile_responsive=bool(soup.find('meta', attrs={'name': 'viewport'})),
            accessibility_score=90.0
            # ... and 28 more metrics ...
        )
        db.session.add(simulated_audit)
        db.session.commit()
    except Exception as e:
        print(f"Audit failed for {website.url}: {e}")
        # Log failure
        db.session.add(Audit(website_id=website.id, load_time=0.0, seo_score=0.0, accessibility_score=0.0, status_code=0))
        db.session.commit()


def daily_audit_all():
    # Runs audit_website for all users' websites
    for website in Website.query.all():
        audit_website_wrapper.delay(website.id)


def send_scheduled_reports():
    # Checks all users and sends reports if schedule matches the current time
    now = datetime.now()
    users = User.query.all()
    
    for user in users:
        freq = user.report_frequency
        time_str = user.report_time
        if not time_str: continue

        hour, minute = map(int, time_str.split(':'))
        
        should_send = False
        if now.hour == hour and now.minute == minute:
            if freq == 'daily':
                should_send = True
            elif freq == 'weekly' and now.strftime('%A') == user.report_day:
                should_send = True
            elif freq == 'monthly' and now.day == 1:
                should_send = True
        
        if should_send:
            websites = Website.query.filter_by(user_id=user.id).all()
            if websites:
                # Generate combined PDF
                html = render_template('report_combined.html', user=user, websites=websites, now=datetime.now)
                pdf = HTML(string=html).write_pdf()
                
                # Send Email (You need to configure your SMTP settings here)
                msg = MIMEMultipart()
                msg['From'] = 'your-report-email@gmail.com' 
                msg['To'] = user.email
                msg['Subject'] = f"37-Metrics Website Report - {freq.title()} ({now.strftime('%Y-%m-%d')})"
                
                body = f"Dear {user.name},\n\nYour {freq} report with all 37 quality metrics is attached.\n\nBest,\nWebsite Quality Team"
                msg.attach(MIMEText(body, 'plain'))
                
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(pdf)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="37Metrics_Report.pdf"')
                msg.attach(part)
                
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login('your-report-email@gmail.com', 'your-app-password') # REPLACE WITH YOUR EMAIL/PASS
                    server.sendmail(msg['From'], user.email, msg.as_string())
                    server.quit()
                    print(f"Report sent successfully to {user.email}")
                except Exception as e:
                    print(f"Email failed for {user.email}: {e}")

# --- Celery Task Wrappers (Defined in celery_worker.py) ---
from celery_worker import audit_website_wrapper # Ensure this import is below the audit_website function definition

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
