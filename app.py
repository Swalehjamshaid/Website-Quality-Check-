# app.py  ← FINAL VERSION THAT DOES REAL AUDITS
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from supabase import create_client
from tasks.run_full_audit import run_full_audit

# Supabase (make sure you have SUPABASE_ANON_KEY in Vercel env vars)
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY", "")
)

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/audit", methods=["POST"])
    def start_audit():
        url = request.json.get("url", "").strip()
        if not url:
            return jsonify({"error": "URL required"}), 400
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # This now runs the REAL audit in background
        task = run_full_audit.delay(url)

        # Save to Supabase (optional but nice)
        try:
            supabase.table("audits").insert({
                "url": url,
                "task_id": task.id,
                "status": "pending"
            }).execute()
        except:
            pass

        return jsonify({"task_id": task.id}), 202

    @app.route("/status/<task_id>")
    def get_status(task_id):
        task_result = run_full_audit.AsyncResult(task_id)

        if task_result.state == "PENDING":
            return jsonify({"state": "PENDING", "progress": 10})
        elif task_result.state == "PROGRESS":
            return jsonify({"state": "PROGRESS", "progress": task_result.info})
        elif task_result.state == "SUCCESS":
            result = task_result.get()
            return jsonify(result)
        else:
            return jsonify({"state": task_result.state, "progress": 0})

    @app.route("/reports/<path:filename>")
    def serve_report(filename):
        return send_from_directory("static/reports", filename, as_attachment=True)

    return app

# Local development
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

# VERCEL NEEDS THIS LINE
app = create_app()
