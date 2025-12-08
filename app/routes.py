from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db, bcrypt
from .models import User, Website, Audit
from .audit_engine import run_all_metrics
import os
import json

main_bp = Blueprint("main", __name__)

# --- simple login view (very small auth for admin convenience)
@main_bp.route("/login", methods=["GET", "POST"])
def login():
    from flask import current_app
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

@main_bp.route("/")
@login_required
def dashboard():
    sites = Website.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", sites=sites, name=current_user.name or "User")

@main_bp.route("/add", methods=["POST"])
@login_required
def add_site():
    url = request.form.get("url", "").strip()
    name = request.form.get("name") or url
    if not url:
        flash("URL required", "danger")
        return redirect(url_for("main.dashboard"))
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    site = Website(url=url, name=name, user_id=current_user.id)
    db.session.add(site)
    db.session.commit()

    # trigger celery task (the celery instance will be provided by wsgi)
    try:
        from wsgi import celery
        celery.send_task("run_full_audit_task", args=[site.id])
    except Exception:
        # fallback: try import run_all_metrics synchronously (for local debug)
        res = run_all_metrics(site.url, pagespeed_api_key=os.getenv("PAGESPEED_API_KEY"))
        audit = Audit(website_id=site.id, data=json.dumps(res))
        db.session.add(audit)
        db.session.commit()
    flash("Site added and audit started", "success")
    return redirect(url_for("main.dashboard"))

@main_bp.route("/results/<int:site_id>")
@login_required
def results(site_id):
    site = Website.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        return redirect(url_for("main.dashboard"))
    latest = Audit.query.filter_by(website_id=site_id).order_by(Audit.created_at.desc()).first()
    if not latest:
        flash("No audit yet. Background job may still be running.", "warning")
        audit = {}
    else:
        try:
            audit = latest.data if isinstance(latest.data, dict) else json.loads(latest.data)
        except Exception:
            audit = {"raw": latest.data}
    return render_template("results.html", site=site, audit=audit)

@main_bp.route("/download/<int:site_id>")
@login_required
def download(site_id):
    flash("PDF download currently disabled for stability.", "warning")
    return redirect(url_for("main.results", site_id=site_id))
