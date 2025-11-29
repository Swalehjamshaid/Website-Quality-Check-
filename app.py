import os
from flask import Flask, render_template, request, jsonify, send_from_directory

# Safe Supabase mock/fallback
class MockSupabase:
    def table(self, name):
        return self
    def insert(self, data):
        return self
    def execute(self):
        return {'data': [], 'error': None}

supabase = MockSupabase()
try:
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        from supabase import create_client
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
except Exception as e:
    print(f"Supabase init failed (using mock): {e}")

# Safe Celery mock/fallback
class MockCelery:
    def delay(self, url):
        # Run the audit immediately (sync for Vercel)
        from tasks.run_full_audit import run_full_audit_func  # Direct function call
        result = run_full_audit_func(url)
        class MockTask:
            id = 'mock-task-' + str(hash(url))
        mock_task = MockTask()
        mock_task.result = result
        return mock_task
    def AsyncResult(self, task_id):
        class MockResult:
            state = 'SUCCESS'
            def get(self):
                return self.result
        return MockResult()

celery = MockCelery()
use_mock = os.getenv("USE_MOCK_CELERY", "true").lower() == "true"
if not use_mock and os.getenv("CELERY_BROKER_URL") and 'localhost' not in os.getenv("CELERY_BROKER_URL"):
    try:
        from celery import Celery
        celery = Celery(
            'website_audit',
            broker=os.getenv("CELERY_BROKER_URL"),
            backend=os.getenv("CELERY_RESULT_BACKEND")
        )
        from tasks.run_full_audit import run_full_audit
    except Exception as e:
        print(f"Celery init failed (using mock): {e}")

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/audit', methods=['POST'])
    def start_audit():
        data = request.get_json() or {}
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': 'URL required'}), 400
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Use real Celery or mock
        if use_mock:
            task = celery.delay(url)
        else:
            task = run_full_audit.delay(url)

        # Safe Supabase insert
        try:
            supabase.table('audits').insert({'url': url, 'task_id': task.id, 'status': 'pending'}).execute()
        except:
            pass

        return jsonify({'task_id': task.id}), 202

    @app.route('/status/<task_id>')
    def get_task_status(task_id):
        # Use real or mock
        if use_mock:
            task = celery.AsyncResult(task_id)
        else:
            task = run_full_audit.AsyncResult(task_id)

        if task.state == 'SUCCESS':
            result = task.get()
            # Generate PDF
            try:
                from tasks.reporting.report_generator import generate_pdf_report
                pdf_path = generate_pdf_report(result)
                result['report_url'] = f'/reports/{os.path.basename(pdf_path)}'
            except:
                result['report_url'] = None
            return jsonify(result)
        return jsonify({'state': task.state, 'progress': task.info.get('progress', 0) if task.info else 0})

    @app.route('/reports/<filename>')
    def download_report(filename):
        return send_from_directory('static/reports', filename, as_attachment=True)

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'celery_mode': 'mock' if use_mock else 'real'})

    return app

# Local run
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)

# VERCEL REQUIRES THIS TOP-LEVEL APP
app = create_app()
