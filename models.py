# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    
    # Report scheduling
    report_frequency = db.Column(db.String(20), default='weekly')  # daily, weekly, monthly
    report_time = db.Column(db.String(5), default='09:00')         # 24-hour format
    report_day = db.Column(db.String(10), default='Monday')        # for weekly/monthly

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # 37 Worldwide Metrics
    load_time = db.Column(db.Float)
    fcp = db.Column(db.Float)
    lcp = db.Column(db.Float)
    cls = db.Column(db.Float)
    tbt = db.Column(db.Float)
    fid = db.Column(db.Float)
    tti = db.Column(db.Float)
    page_size_kb = db.Column(db.Float)
    requests_count = db.Column(db.Integer)
    speed_index = db.Column(db.Float)
    server_response_time = db.Column(db.Float)
    dom_loaded_time = db.Column(db.Float)

    seo_score = db.Column(db.Float)
    has_meta_desc = db.Column(db.Boolean)
    title_length = db.Column(db.Integer)
    h1_count = db.Column(db.Integer)
    has_canonical = db.Column(db.Boolean)
    robots_valid = db.Column(db.Boolean)
    has_sitemap = db.Column(db.Boolean)
    keyword_density = db.Column(db.Float)

    accessibility_score = db.Column(db.Float)
    alt_text_ratio = db.Column(db.Float)
    contrast_ratio = db.Column(db.Float)
    aria_labels_count = db.Column(db.Integer)
    heading_structure = db.Column(db.Boolean)
    form_labels_ratio = db.Column(db.Float)
    keyboard_score = db.Column(db.Float)

    has_https = db.Column(db.Boolean)
    security_headers_count = db.Column(db.Integer)
    ssl_days_left = db.Column(db.Integer)
    mixed_content_issues = db.Column(db.Integer)

    broken_links = db.Column(db.Integer)
    mobile_responsive = db.Column(db.Boolean)
    bounce_rate = db.Column(db.Float)
    avg_session_duration = db.Column(db.Float)
    images_optimized_ratio = db.Column(db.Float)
    cwv_pass_rate = db.Column(db.Float)

    raw_data = db.Column(db.JSON)
