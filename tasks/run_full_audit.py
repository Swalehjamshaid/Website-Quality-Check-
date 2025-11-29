# app.py → FINAL VERSION WITH REAL AUDITS
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from tasks.run_full_audit import run_full_audit   # ← this is the real task

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

        task = run_full_audit.delay(url)          # ← REAL background audit
        return jsonify({"task_id": task.id}), 202

    @app.route("/status/<task_id>")
    def status(task_id):
        task = run_full_audit.AsyncResult(task_id)

        if task.state == "SUCCESS":
            return jsonify(task.get())            # ← returns real results + PDF link
        else:
            return jsonify({
                "state": task.state,
                "progress": task.info.get("progress", 0) if task.info else 0
            })

    @app.route("/reports/<path:filename>")
    def reports(filename):
        return send_from_directory("static/reports", filename)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

app = create_app()   # ← Vercel needs this line
