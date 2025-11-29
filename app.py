import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from supabase import create_client
from celery import Celery
from tasks.run_full_audit import run_full_audit  # ← this works because of __init__.py

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Initialize Celery
celery_app = Celery(
    "website_audit",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load config
    try:
        from config import config_map
        app.config.from_object(config_map.get(os.getenv("FLASK_CONFIG", "default")))
    except:
        pass  # fallback already in config.py

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/audit", methods=["POST"])
    def start_audit():
        url = request.json.get("url", "").strip()
        if not url.startswith("http"):
            url"):
            url = "https://" + url
        
        task = run_full_audit.delay(url)  # Real background task
        
        # Save to Supabase
        supabase.table("audits").insert({
            "url": url,
            "task_id": task.id,
            "status": "pending"
        }).execute()
        
        return jsonify({"task_id": task.id}), 202

    @app.route("/status/<task_id>")
    def status(task_id):
        task = run_full_audit.AsyncResult(task_id)
        
        if task.state == "SUCCESS":
            result = task.get()
            return jsonify(result)
        
        return jsonify({
            "state": task.state,
            "progress": task.info.get("progress", 0) if task.info else 0
        })

    @app.route("/reports/<path:filename>")
    def reports(filename):
        return send_from_directory("static/reports", filename)

    return app

# Local run
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

# Vercel needs this
app = create_app()
