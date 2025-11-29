# app.py — FINAL VERSION THAT WORKS 100% WITH audit_engine.py
import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory

# REQUIRED FOR VERCEL
application = Flask(__name__, template_folder="templates", static_folder="static")
app = application

# In-memory storage
results = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/audit", methods=["POST"])
def start_audit():
    try:
        data = request.get_json() or {}
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "Please enter a URL"}), 400
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        task_id = str(uuid.uuid4())

        # THIS IS THE ONLY CORRECT IMPORT — WORKS 100%
        from tasks.audit_engine import perform_real_audit
        result = perform_real_audit(url)

        result["task_id"] = task_id
        result["state"] = "SUCCESS"
        results[task_id] = result

        # Generate PDF (optional)
        try:
            from tasks.reporting.report_generator import generate_pdf_report
            os.makedirs("static/reports", exist_ok=True)
            temp_pdf = generate_pdf_report(result)
            final_pdf = f"static/reports/report_{task_id}.pdf"
            os.replace(temp_pdf, final_pdf)
            result["report_url"] = f"/reports/report_{task_id}.pdf"
        except Exception as e:
            print("PDF generation failed:", e)
            result["report_url"] = None

        return jsonify({"task_id": task_id}), 202

    except Exception as e:
        return jsonify({"error": "Server error: " + str(e)}), 500

@app.route("/status/<task_id>")
def status(task_id):
    if task_id not in results:
        return jsonify({"state": "PENDING"}), 200
    return jsonify(results[task_id])

@app.route("/reports/<filename>")
def download_report(filename):
    try:
        return send_from_directory("static/reports", filename, as_attachment=True)
    except:
        return "Report not found", 404

# Health check
@app.route("/health")
def health():
    return "OK", 200
