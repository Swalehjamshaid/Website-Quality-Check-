from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import shutil

# Correct paths when running from /api folder
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

results = {}

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

        task_id = str(uuid.uuid4())

        from tasks.audit_engine import perform_real_audit
        data = perform_real_audit(url)
        data["task_id"] = task_id
        data["url"] = url

        # PDF
        try:
            from tasks.reporting.report_generator import generate_pdf_report
            os.makedirs(os.path.join(BASE_DIR, "static", "reports"), exist_ok=True)
            pdf_path = generate_pdf_report(data)
            final_pdf = os.path.join(BASE_DIR, "static", "reports", f"report_{task_id}.pdf")
            shutil.move(pdf_path, final_pdf)
            data["report_url"] = f"/reports/report_{task_id}.pdf"
        except Exception as e:
            data["report_url"] = None

        results[task_id] = data
        return jsonify({"task_id": task_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<task_id>")
def status(task_id):
    return jsonify(results.get(task_id, {"status": "not found"}))

@app.route("/reports/<path:filename>")
def reports(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static", "reports"), filename)

# Required by Vercel
handler = app
