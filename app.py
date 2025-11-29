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
    Config = None
    try:
        from config import config_map
        Config = config_map.get(config_name, config_map["default"])
    except Exception as e:
        print(f"Config import failed: {e}, using minimal safe config")
        # FIXED: This class is now properly defined inside the except block with correct indentation
        class FallbackConfig:
            DEBUG = False
            TESTING = False
            SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
            SUPABASE_URL = os.getenv("SUPABASE_URL", "")
            CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")
        Config = FallbackConfig()

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
                os.getenv("SUPABASE_ANON_KEY", "")  # Add SUPABASE_ANON_KEY to Vercel env vars if using real Supabase
            )
            print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Supabase init failed (using mock): {e}")

    try:
        if os.getenv("CELERY_BROKER_URL") and os.getenv("CELERY_BROKER_URL") != "redis://localhost:6379/0":
            from celery import Celery
            global celery
            celery = Celery(
                app.name,
                broker=os.getenv("CELERY_BROKER_URL"),
                backend=os.getenv("CELERY_RESULT_BACKEND", os.getenv("CELERY_BROKER_URL"))
            )
            print("Celery client initialized successfully")
    except Exception as e:
        print(f"Celery init failed (using mock): {e}")

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
        print(f"Audit started for URL: {url}")  # Log for Vercel debugging
        return jsonify({
            "status": "Audit queued",
            "task_id": "mock-task-12345",
            "url": url
        }), 202

    @app.route('/status/<task_id>')
    def get_task_status(task_id):
        # Mock instant success for frontend testing
        print(f"Status check for task: {task_id}")  # Log for Vercel debugging
        return jsonify({
            "task_id": task_id,
            "state": "SUCCESS",
            "progress": 100,
            "status": "Audit completed (mock)",
            "audit_id": "mock-audit-999"
        })

    @app.route('/health')
    def health():
        return jsonify({
            "status": "ok", 
            "env": config_name,
            "supabase_available": bool(os.getenv("SUPABASE_URL")),
            "celery_available": bool(os.getenv("CELERY_BROKER_URL"))
        })

    return app


# ────────────────────── Entry Points ──────────────────────
# Local development
if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    print(f"Running on http://0.0.0.0:{port}")

# VERCEL: This line is MANDATORY — creates the app instance Vercel expects
# It must be at module level (not inside any function/block)
app = create_app()
