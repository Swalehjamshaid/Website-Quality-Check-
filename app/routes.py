# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from . import db, bcrypt
from .models import User, Website, Audit
from .tasks import audit_website

bp = Blueprint('routes', __name__)

# ... put all your @app.route functions here using @bp.route ...
# Example:
@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    return redirect(url_for('routes.login'))
