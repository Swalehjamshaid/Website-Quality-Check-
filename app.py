import os
from flask import Flask, jsonify, request, render_template

# --- 1. Real Service Imports ---
# We use try/except to allow this file to be run locally without these packages installed 
# IF you were not using Celery or Supabase in development. But for Vercel, they are required.
from supabase import create_client
from celery import Celery
import uuid
import datetime

# --- Global Initialization (Supabase client must be created globally in this pattern) ---
# NOTE: This assumes SUPABASE_URL and SUPABASE_SERVICE_KEY are set in environment variables!
try:
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    else:
        # If keys are missing, use a mock/None object to prevent crash
        class MockSupabase:
            def table(self, table_name): return self
            def insert(self, data): return self
            def execute(self): return {'data': [], 'error': None}
        supabase = MockSupabase()
except Exception:
    class MockSupabase:
        def table(self, table_name): return self
        def insert(self, data): return self
        def execute(self): return {'data': [], 'error': None}
    supabase = MockSupabase()


# --- Application Factory ---

def create_app(config_name='default'):
    """
    Application factory function. Creates and configures the Flask app.
    """
    
    # 1. Load Configuration SAFELY
    try:
        from config import config_map
        Config = config_map.get(config_name, config_map['default'])
    except Exception as e:
        print(f"FATAL: Configuration load error: {e}")
        return Flask(__name__) 

    # 2. Initialize Flask App
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )
    app.config.from_object(Config)

    # 3. Initialize Celery (Uses app config)
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)
    
    # CRITICAL: Import tasks *after* Celery is initialized
    try:
        from tasks.run_full_audit import run_full_audit
    except ImportError:
        # If tasks fail to import, the app still runs, but the tasks are mocked below.
        print("Warning: Could not import run_full_audit task.")
        run_full_audit = None
        
    # 4. Register Routes
    
    @app.route('/')
    def index():
        """Renders the main dashboard page."""
        return render_template('index.html')

    @app.route('/audit', methods=['POST'])
    def start_audit():
        """Starts the real Celery audit task."""
        data = request.get_json()
        url = data.get('url', 'N/A')
        
        if run_full_audit:
            # Call the real Celery task
            task = run_full_audit.delay(url)
            return jsonify({
                'status': 'Audit started',
                'task_id': task.id,
                'url': url
            }), 202
        else:
            # Fallback to mock if Celery is not running/task failed to import
             return jsonify({
                'status': 'Mock audit started (Celery offline)',
                'task_id': str(uuid.uuid4()),
                'url': url
            }), 202


    @app.route('/status/<task_id>', methods=['GET'])
    def get_task_status(task_id):
        """Checks the real status of a running task."""
        
        # NOTE: If Celery is not running, this will return PENDING forever.
        if run_full_audit:
            task = run_full_audit.AsyncResult(task_id)

            if task.state == 'PENDING':
                response = {'state': task.state, 'progress': 0, 'status': 'Waiting to start...'}
            elif task.state != 'FAILURE':
                response = {
                    'state': task.state,
                    'progress': task.info.get('progress', 0),
                    'status': task.info.get('status', 'Processing...')
                }
                if 'audit_id' in task.info:
                    response['audit_id'] = task.info['audit_id']
                    response['status'] = 'Complete'
            else:
                response = {'state': task.state, 'status': str(task.info), 'progress': 100}
            return jsonify(response)
        
        # Mocks a successful completion instantly if tasks are disabled
        return jsonify({'state': 'SUCCESS', 'progress': 100, 'status': 'Mock Complete', 'audit_id': 'MOCK-AUDIT-ID'}), 200


    return app

# --- Local Entry Point ---
# Only called when running locally via 'python app.py'
if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000)
