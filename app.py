import os
from flask import Flask, jsonify, request, render_template

# Placeholder classes/objects to prevent crashing on import when not running locally
# These mocks prevent 'NameError' if external files import them globally.
class MockService:
    def __init__(self, *args, **kwargs):
        pass
    def table(self, table_name):
        return self
    def insert(self, data):
        return self
    def execute(self):
        # Mock successful execution
        return {'data': [], 'error': None}
    
# Initialize global mocks for safety
# NOTE: These must be imported by your tasks/reporting files if they use them globally.
supabase = MockService()
celery = MockService() 


# --- Application Factory ---

def create_app(config_name='default'):
    """
    Application factory function. Creates and configures the Flask app.
    This pattern ensures the app starts cleanly in environments like Vercel.
    """
    
    # 1. CRITICAL FIX: Load Configuration SAFELY INSIDE the function
    try:
        # Import config_map here to prevent the global NameError crash
        from config import config_map
        # Safely get configuration, defaulting to 'default' if config_name is invalid
        Config = config_map.get(config_name, config_map['default'])
    except Exception as e:
        # This fallback prevents the server from returning a 500 error due to config file issues
        print(f"FATAL: Configuration load error: {e}")
        return Flask(__name__) 

    # 2. Initialize Flask App
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )
    app.config.from_object(Config)

    # 3. Register Routes
    
    @app.route('/')
    def index():
        """Renders the main dashboard page."""
        return render_template('index.html')

    @app.route('/audit', methods=['POST'])
    def start_audit():
        """Mocked route to start the audit."""
        data = request.get_json()
        url = data.get('url', 'N/A')
        
        # In a real app, you would call: task = run_full_audit.delay(url)
        return jsonify({
            'status': 'Mock audit started',
            'task_id': 'MOCKID-12345',
            'url': url
        }), 202

    @app.route('/status/<task_id>', methods=['GET'])
    def get_task_status(task_id):
        """Mocked route to check the status."""
        
        # Mocks a successful completion instantly for testing the frontend flow
        return jsonify({
            'state': 'SUCCESS',
            'progress': 100,
            'status': 'Mock Complete',
            'audit_id': 'MOCK-AUDIT-ID'
        }), 200

    return app

# --- Local Entry Point ---
# Only called when running locally via 'python app.py'
if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000)
