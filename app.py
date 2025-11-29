# app.py

import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_file, render_template

from celery import Celery
from config import config_map

# 🚨 COMMENT OUT OR TEMPORARILY REMOVE SUPABASE INITIALIZATION
# from supabase import create_client, client
# supabase: client = create_client(
#     os.environ.get('SUPABASE_URL'), 
#     os.environ.get('SUPABASE_SERVICE_KEY')
# )

# --- 1. App and Celery Initialization ---
config_name = os.environ.get('FLASK_CONFIG', 'default')
Config = config_map[config_name]

app = Flask(
    __name__, 
    static_folder='static', 
    template_folder='templates'
)
app.config.from_object(Config)

# 🚨 COMMENT OUT THIS ENTIRE CELERY BLOCK FOR DEPLOYMENT TESTING!
# Celery Initialization
# celery = Celery(
#     app.import_name,
#     backend=app.config['CELERY_RESULT_BACKEND'],
#     broker=app.config['CELERY_BROKER_URL']
# )
# celery.conf.update(app.config)

# --- 2. Import Tasks ---
# 🚨 COMMENT OUT THE TASK IMPORT
# from tasks.run_full_audit import run_full_audit

# --- 3. Frontend Route ---
@app.route('/')
def index():
    """Renders the main dashboard page."""
    # This is the only route we need to test the basic server startup
    return render_template('index.html')

# --- 4. API Routes for Audit Management ---

# 🚨 TEMPORARILY REMOVE OR COMMENT OUT THESE ROUTES
# @app.route('/audit', methods=['POST'])
# def start_audit():
#     # ... code that requires Celery ...
#     pass

# @app.route('/status/<task_id>', methods=['GET'])
# def get_task_status(task_id):
#     # ... code that requires Celery ...
#     pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
