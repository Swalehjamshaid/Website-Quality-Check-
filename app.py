import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__, template_folder="templates", static_folder="static")

# Simple in-memory storage (works perfectly on Vercel)
results_store = {}

# Your real audit function (direct call, no Celery needed)
def run_real_audit(url):
    try:
        from tasks.run_full_audit import run_full_audit_func
        return run_full_audit_func(url)
    except Exception as e:
        return {
            "url": url,
            "score": 15,
            "summary": "Audit failed – server issue",
            "details": {"error": str(e)}
        }

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
        print(f"Starting audit for {url} → task {task_id}")

        # Run audit immediately (fast & reliable on Vercel)
        result = run_real_audit(url)
        result["task_id"] = task_id
        results_store[task_id] = result

        return jsonify({"task_id": task_id}), 202
    except Exception as e:
        return jsonify({"error": "Server error", "msg": str(e)}), 500

@app.route("/status/<task_id>")
def status(task_id):
    try:
        if task_id not in results_store:
            return jsonify({"state": "PENDING"}), 200

        result = results_store[task_id]
        result["state"] = "SUCCESS"

        # Generate PDF if you have the function
        try:
            from tasks.reporting.report_generator import generate_pdf_report
            pdf_path = generate_pdf_report(result)
            result["report_url"] = f"/reports/{os.path.basename(pdf_path)}"
        except:
            result["report_url"] = None

        return jsonify(result)
    except Exception as e:
        return jsonify({"state": "FAILURE", "error": str(e)}), 500

@app.route("/reports/<path:filename>")
def reports(filename):
    try:
        return send_from_directory("static/reports", filename, as_attachment=True)
    except:
        return "Report not found", 404

# Required for Vercel
if __name__ != "__main__":
    app = app
