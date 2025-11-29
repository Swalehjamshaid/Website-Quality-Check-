# app.py

import os
from flask import Flask, jsonify, request, render_template

from config import config_map

# 🚨 TEMPORARY: Define a placeholder for services that aren't running on Vercel
# You will need to replace these with actual initialized objects later.
# For now, let's just make sure the code doesn't crash on import.
# Note: You need to set 'celery' and 'supabase' to None or a placeholder if other files import them.
celery = None
supabase = None

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
    # NOTE: You must define your routes INSIDE this function or register them using blueprints.
    
    @app.route('/')
    def index():
        return render_template('index.html')

    # 4. Register API Routes (Temporarily simple/mocked for deployment test)
    # 🚨 This is the simplest possible version to test if the route works.
    @app.route('/audit', methods=['POST'])
    def start_audit():
        return jsonify({'status': 'Mock audit started (Celery not running)', 'task_id': 'MOCKID'}), 202

    @app.route('/status/<task_id>', methods=['GET'])
    def get_task_status(task_id):
        return jsonify({'state': 'SUCCESS', 'progress': 100, 'status': 'Mock Complete'}), 200

    return app

# If you need to run locally, call the factory function
if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000)
