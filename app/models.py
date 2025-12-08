from datetime import datetime
from . import db, login_manager
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSON
from flask import current_app

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), default="User")
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    websites = db.relationship("Website", backref="owner", lazy=True)

class Website(db.Model):
    __tablename__ = "website"
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(800), nullable=False)
    name = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    audits = db.relationship("Audit", backref="website", lazy=True)

class Audit(db.Model):
    __tablename__ = "audit"
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey("website.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # JSON column if using postgres, fallback to Text
    try:
        data = db.Column(JSON)
    except Exception:
        data = db.Column(db.Text)

# flask-login loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
