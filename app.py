# app.py
import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_file, render_template
from celery import Celery
from supabase import create_client, Client
from .config import Config

# --- 1. App Initialization ---
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(Config)

# --- 2. Supabase Initialization (using the SERVICE_KEY for backend operations) ---
# NOTE: The public 'anon' key is often used for client-side, but the SERVICE_KEY 
# is needed here for full, bypass-RLS backend access to save audit data.
supabase: Client = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_SERVICE_KEY'])

# --- 3. Celery Initialization ---
celery = Celery(
    app.import_name,
    backend=app.config['CELERY_RESULT_BACKEND'],
    broker=app.config['CELERY_BROKER_URL']
)
celery.conf.update(app.config)

# --- 4. Import Tasks and Reporting ---
from .tasks import run_full_audit
from .reporting import generate_pdf_report

# --- 5. Flask Routes ---

@app.route('/')
def index():
    """Serves the main dashboard HTML page."""
    return render_template('index.html')

@app.route('/api/websites', methods=['GET', 'POST'])
def handle_websites():
    if request.method == 'POST':
        # --- Add New Website ---
        data = request.json
        url = data.get('url')
        schedule = data.get('schedule', 'manual')
        
        if not url:
            return jsonify({"message": "URL is required"}), 400

        try:
            # Insert website into Supabase 'websites' table
            supabase_response = supabase.table("websites").insert({
                "url": url,
                "schedule_interval": schedule,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            new_website_id = supabase_response.data[0]['id']
            
            # Trigger the first audit
            task = run_full_audit.delay(new_website_id)
            
            return jsonify({
                "message": "Website added successfully. Audit initiated.",
                "website_id": new_website_id,
                "task_id": task.id
            }), 201
        except Exception as e:
            app.logger.error(f"Error adding website: {e}")
            return jsonify({"message": "Database insertion error", "details": str(e)}), 500

    elif request.method == 'GET':
        # --- Fetch Website Summary for Dashboard ---
        try:
            # Fetch websites and related audit results (assuming you have foreign key linking)
            # This complex query is simplified by fetching related data with select:
            websites_data = supabase.table("websites").select(
                "id, url, schedule_interval, created_at, audit_results(id, timestamp, performance_score, seo_score, raw_data)"
            ).execute().data
            
            # Process to attach ONLY the latest result for cleaner JS consumption
            for site in websites_data:
                results = site.pop('audit_results', [])
                if results:
                    results.sort(key=lambda x: x['timestamp'], reverse=True)
                    site['latest_result'] = results[0]
                else:
                    site['latest_result'] = None

            return jsonify(websites_data), 200
        except Exception as e:
            return jsonify({"message": "Error fetching summary data", "details": str(e)}), 500


@app.route('/api/audit/<int:website_id>', methods=['POST'])
def trigger_audit(website_id):
    """Triggers an on-demand audit."""
    try:
        # Check existence before starting the long task
        website = supabase.table("websites").select("id").eq("id", website_id).execute().data
        if not website:
            return jsonify({"message": "Website not found"}), 404
            
        task = run_full_audit.delay(website_id)
        return jsonify({
            "message": f"Audit initiated for ID {website_id}", 
            "task_id": task.id
        }), 202
    except Exception as e:
        return jsonify({"message": "Error triggering audit", "details": str(e)}), 500


@app.route('/api/report/pdf/<int:result_id>', methods=['GET'])
def download_pdf(result_id):
    """Downloads a PDF report."""
    try:
        # Fetch audit result data from Supabase
        result_data = supabase.table("audit_results").select("*, websites(url)").eq("id", result_id).execute().data
        if not result_data:
            return jsonify({"error": "Audit result not found"}), 404
            
        # Call the reporting module to generate the PDF
        pdf_stream = generate_pdf_report(result_data[0])

        if pdf_stream:
            return send_file(
                pdf_stream,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'audit_report_{result_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
        return jsonify({"error": "Report generation failed"}), 500
        
    except Exception as e:
        app.logger.error(f"Error generating PDF: {e}")
        return jsonify({"error": "Internal error during report generation", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
