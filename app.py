import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory

# REQUIRED FOR VERCEL
application = Flask(__name__, template_folder="templates", static_folder="static")
app = application

results = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/audit", methods=["POST"])
def start_audit():
    try:
        url = (request.get_json() or {}).get("url", "").strip()
        if not url:
            return jsonify({"error": "URL required"}), 400
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        task_id = str(uuid.uuid4())

        # THIS IS THE ONLY CORRECT LINE — NO run_full_audit ANYWHERE
        from tasks.run_full_audit import run_full_audit_func
        result = run_full_audit_func(url)

        result["task_id"] = task_id
        result["state"] = "SUCCESS"
        results[task_id] = result

        # PDF
        try:
            from tasks.reporting.report_generator import generate_pdf_report
            os.makedirs("static/reports", exist_ok=True)
            pdf_path = generate_pdf_report(result)
            os.replace(pdf_path, f"static/reports/report_{task_id}.pdf")
            result["report_url"] = f"/reports/report_{task_id}.pdf"
        except:
            result["report_url"] = None

        return jsonify({"task_id": task_id}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<task_id>")
def status(task_id):
    return jsonify(results.get(task_id, {"state": "PENDING"}))

@app.route("/reports/<filename>")
def download(filename):
    return send_from_directory("static/reports", filename, as_attachment=True)
