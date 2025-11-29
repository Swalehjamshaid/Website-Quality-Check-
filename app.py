import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from celery import Celery

# Celery setup (safe fallback if no broker)
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=os.getenv('CELERY_RESULT_BACKEND'),
        broker=os.getenv('CELERY_BROKER_URL')
    )
    celery.conf.update(app.config)
    return celery

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # Mock task if no Celery (for testing)
    class MockTask:
        def delay(self, url):
            return self
        def AsyncResult(self, id):
            class MockResult:
                state = 'SUCCESS'
                def get(self):
                    return {'url': url, 'score': 85, 'checks': {'HTTP Status': 'PASS', 'Title': 'PASS'}}
            return MockResult()
    
    celery = MockTask()  # Fallback
    if os.getenv('CELERY_BROKER_URL') and 'localhost' not in os.getenv('CELERY_BROKER_URL'):
        celery = make_celery(app)
        from tasks.run_full_audit import run_full_audit  # Real task
    else:
        print("Using mock task - set real Redis for production")

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

        task = run_full_audit.delay(url) if 'run_full_audit' in globals() else celery.delay(url)
        return jsonify({"task_id": task.id if hasattr(task, 'id') else 'mock-task'}), 202

    @app.route("/status/<task_id>")
    def status(task_id):
        task = run_full_audit.AsyncResult(task_id) if 'run_full_audit' in globals() else celery.AsyncResult(task_id)
        if task.state == "SUCCESS":
            return jsonify(task.get())
        else:
            return jsonify({"state": task.state, "progress": 0})

    return app

app = create_app()
