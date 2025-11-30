# app.py
import os
import uuid
import shutil
from flask import Flask, render_template, request, jsonify, send_from_directory

# THIS LINE IS CRITICAL FOR VERCEL
application = Flask(__name__, template_folder="templates", static_folder="static")
app = application

# In-memory storage (Vercel is stateless, so results don't persist long-term)
results_store = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/audit", methods=["POST"])
def start_audit():
    try:
        data = request.get_json()
        url = data.get("url", "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        task_id = str(uuid.uuid4())

        # Lazy import – fixes cold start & Vercel compatibility
        from tasks.audit_engine import perform_real_audit

        audit_result = perform_real_audit(url)
        audit_result["task_id"] = task_id
        audit_result["url"] = url
        audit_result["state"] = "SUCCESS"

        # Generate PDF Report
        try:
            from tasks.reporting.report_generator import generate_pdf_report
            os.makedirs("static/reports", exist_ok=True)
            pdf_path = generate_pdf_report(audit_result)
            final_path = f"static/reports/report_{task_id}.pdf"
            shutil.move(pdf_path, final_path)
            audit_result["report_url"] = f"/reports/report_{task_id}.pdf"
        except Exception as pdf_error:
            print("PDF generation failed:", pdf_error)
            audit_result["report_url"] = None

        # Save result
        results_store[task_id] = audit_result

        return jsonify({"task_id": task_id, "status": "processing"}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<task_id>")
def status(task_id):
    result = results_store.get(task_id)
    if result:
        return jsonify(result)
    else:
        return jsonify({"state": "PENDING", "task_id": task_id})

@app.route("/reports/<filename>")
def download_report(filename):
    try:
        return send_from_directory("static/reports", filename, as_attachment=True)
    except Exception:
        return "Report not found", 404

# Health check for Vercel
@app.route("/health")
def health():
    return "OK", 200

# Run only locally
if __name__ == "__main__":
    app.run(debug=True)
