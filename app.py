import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory

# THIS IS REQUIRED FOR VERCEL
application = Flask(__name__, template_folder="templates", static_folder="static")
app = application

results = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return "OK", 200

@app.route("/audit", methods=["POST"])
def start_audit():
    try:
        url = (request.get_json() or {}).get("url", "").strip()
        if not url:
            return jsonify({"error": "URL required"}), 400
        if not url.startswith("http"):
            url = "https://" + url

        task_id = str(uuid.uuid4())

        # ←←← LAZY IMPORT – THIS IS THE KEY FIX ←←←
        from tasks.audit_engine import perform_real_audit   # moved inside the function
        result = perform_real_audit(url)

        result["task_id"] = task_id
        result["state"] = "SUCCESS"
        results[task_id] = result

        try:
            from tasks.reporting.report_generator import generate_pdf_report
            os.makedirs("static/reports", exist_ok=True)
            pdf_path = generate_pdf_report(result)
            final_path = f"static/reports/report_{task_id}.pdf"
            import shutil
            shutil.move(pdf_path, final_path)
            result["report_url"] = f"/reports/report_{task_id}.pdf"
        except Exception as e:
            print("PDF error:", e)
            result["report_url"] = None

        return jsonify({"task_id": task_id}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<task_id>")
def status(task_id):
    return jsonify(results.get(task_id, {"state": "PENDING", "task_id": task_id}))

@app.route("/reports/<filename>")
def reports(filename):
    return send_from_directory("static/reports", filename, as_attachment=True)
