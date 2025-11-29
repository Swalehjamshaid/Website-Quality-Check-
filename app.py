import os
from flask import Flask, jsonify, request, render_template

from config import config_map

# Placeholder classes/objects to prevent crashing on import when not running locally
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
    
supabase = MockService()
celery = MockService()


# --- Application Factory ---

def create_app(config_name='default'):
    """Application factory function."""
    
    # 1. Load Configuration
    Config = config_map[config_name]
    
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

# --- WSGI Entry Point ---
# Only called when running locally or by development scripts
if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000)
