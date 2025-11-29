# app.py — FINAL PROFESSIONAL VERSION (Full Real Audit + PDF)
import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__, template_folder="templates", static_folder="static")
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
            return jsonify({"error": "Enter a URL"}), 400
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        task_id = str(uuid.uuid4())

        # ←←← REAL FULL AUDIT HAPPENS HERE
        from tasks.run_full_audit import run_full_audit_func
        # ← REAL FUNCTION
        result = run_full_audit_func(url)                               # ← REAL RESULTS

        result["task_id"] = task_id
        result["state"] = "SUCCESS"

        # Generate real PDF
        try:
            from tasks.reporting.report_generator import generate_pdf_report
            os.makedirs("static/reports", exist_ok=True)
            temp_path = generate_pdf_report(result)
            final_path = f"static/reports/report_{task_id}.pdf"
            os.replace(temp_path, final_path)
            result["report_url"] = f"/reports/report_{task_id}.pdf"
        except Exception as e:
            print("PDF failed:", e)
            result["report_url"] = None

        results[task_id] = result
        return jsonify({"task_id": task_id}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<task_id>")
def status(task_id):
    if task_id not in results:
        return jsonify({"state": "PENDING"}), 200
    return jsonify(results[task_id])

@app.route("/reports/<filename>")
def download_report(filename):
    return send_from_directory("static/reports", filename, as_attachment=True)

# REQUIRED BY VERCEL
app = app
