import os
from flask import Flask, jsonify, request, render_template

# ──────────────────────────────────────────────────────────────
# Mock services — they will be replaced at runtime if real ones exist
# This prevents ImportError on Vercel when config fails to load real clients
# ──────────────────────────────────────────────────────────────
class MockService:
    def __init__(self, *args, **kwargs):
        pass
    def table(self, table_name):
        return self
    def insert(self, data):
        return self
    def execute(self):
        return {'data': [], 'error': None}
    def send(self, *args, **kwargs):
        return self

# Default to mocks
supabase = MockService()
celery = MockService()

# ──────────────────────────────────────────────────────────────
# Application Factory
# ──────────────────────────────────────────────────────────────
def create_app():
    # Determine config name from Vercel environment variable
    config_name = os.getenv("FLASK_CONFIG", "production").lower()

    # Try to load real config, fall back safely if anything fails
    try:
        from config import config_map
        Config = config_map.get(config_name, config_map["default"])
    except Exception as e:
        print(f"Config import failed: {e}, using minimal safe config")
        class FallbackConfig:
            DEBUG = False
            TESTING = False
            SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
            SUPABASE_URL = os.getenv("SUPABASE_URL", "")
            CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")
        Config = FallbackConfig

    # Create Flask app
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)

    # ── Initialize real services only if URLs are actually provided ──
    try:
        if os.getenv("SUPABASE_URL"):
            from supabase import create_client
            global supabase
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_ANON_KEY", "")  # add this in Vercel later if needed
            )
    except Exception as e:
        print(f"Supabase init failed (mock used): {e}")

    try:
        if os.getenv("CELERY_BROKER_URL"):
            from celery import Celery
            global celery
            celery = Celery(
                app.name,
                broker=os.getenv("CELERY_BROKER_URL"),
                backend=os.getenv("CELERY_RESULT_BACKEND", os.getenv("CELERY_BROKER_URL"))
            )
    except Exception as e:
        print(f"Celery init failed (mock used): {e}")

    # ────────────────────── Routes ──────────────────────
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/audit', methods=['POST'])
    def start_audit():
        data = request.get_json() or {}
        url = data.get('url', '').strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400

        # In production you would do: run_full_audit.delay(url)
        return jsonify({
            "status": "Audit queued",
            "task_id": "mock-task-12345",
            "url": url
        }), 202

    @app.route('/status/<task_id>')
    def get_task_status(task_id):
        # Mock instant success for frontend testing
        return jsonify({
            "task_id": task_id,
            "state": "SUCCESS",
            "progress": 100,
            "status": "Audit completed (mock)",
            "audit_id": "mock-audit-999"
        })

    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "env": config_name})

    return app


# ────────────────────── Entry Points ──────────────────────
# Local development
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)

# VERCEL: This line is MANDATORY — creates the app instance Vercel expects
app = create_app()
