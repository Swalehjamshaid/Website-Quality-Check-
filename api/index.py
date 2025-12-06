from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import shutil

# Correct paths when running from /api folder
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# CRITICAL: Import the factory and Celery instance from app.py
from app import create_app, celery_app
from tasks.audit_engine import perform_real_audit # Assumed path
from tasks.reporting.report_generator import generate_pdf_report # Assumed path

# --- Celery Task Definition (Wrapper) ---
@celery_app.task(bind=True)
def run_audit_task(self, url):
    # 1. Run the audit
    data = perform_real_audit(url)
    data["task_id"] = self.request.id
    data["url"] = url
    
    # 2. Generate PDF and move it to the reports folder
    try:
        reports_dir = os.path.join(BASE_DIR, "static", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        pdf_path = generate_pdf_report(data)
        final_pdf = os.path.join(reports_dir, f"report_{self.request.id}.pdf")
        shutil.move(pdf_path, final_pdf)
        data["report_url"] = f"/reports/report_{self.request.id}.pdf"
    except Exception as e:
        print(f"PDF generation failed for task {self.request.id}: {e}")
        data["report_url"] = None
        
    return data

# --- Flask Initialization ---
app = create_app()

# --- Flask Routes ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/audit", methods=["POST"])
def audit():
    try:
        url = request.json.get("url", "").strip()
        if not url:
            return jsonify({"error": "No URL"}), 400
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Send the long-running task to Celery
        task = run_audit_task.delay(url)
        
        # Return the Celery task ID immediately
        return jsonify({"task_id": task.id, "status": "pending"}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<task_id>")
def status(task_id):
    task = run_audit_task.AsyncResult(task_id)
    
    response = {
        "task_id": task.id,
        "status": task.status,
    }
    
    if task.state == 'SUCCESS':
        response["result"] = task.result
    elif task.state == 'FAILURE':
        response["error"] = str(task.info)

    return jsonify(response)

@app.route("/reports/<path:filename>")
def reports(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static", "reports"), filename)

handler = app
