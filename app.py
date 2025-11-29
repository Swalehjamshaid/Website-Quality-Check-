# app.py

from flask import Flask, render_template_string, request, jsonify
# 1. Import the task from the new, correct location
from tasks.tasks import run_full_audit
# 2. Import the celery app instance (only needed for status checks)
from tasks.celery_app import celery_app 

app = Flask(__name__)

# --- Simplified HTML/Frontend Setup ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html><body>
    <h1>Quality Check Dashboard</h1>
    <form method="POST" action="/start_audit">
        <input type="text" name="url" value="https://google.com">
        <button type="submit">Run Check</button>
    </form>
    <div id="status_message" style="margin-top: 20px;"></div>
    <script>
    document.querySelector('form').onsubmit = async (e) => {
        e.preventDefault();
        const url = document.querySelector('input[name="url"]').value;
        const statusDiv = document.getElementById('status_message');
        statusDiv.innerHTML = 'Starting audit...';

        const response = await fetch('/start_audit', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: `url=${encodeURIComponent(url)}`
        });
        
        const data = await response.json();
        
        if (response.ok) {
            statusDiv.innerHTML = `Task started! ID: <b>${data.task_id}</b>.`;
            pollStatus(data.task_id);
        } else {
            statusDiv.innerHTML = `Error: ${data.error || 'Failed to start task.'}`;
        }
    };

    function pollStatus(taskId) {
        const statusDiv = document.getElementById('status_message');
        const interval = setInterval(async () => {
            const res = await fetch(`/status/${taskId}`);
            const data = await res.json();
            
            statusDiv.innerHTML = `Status (${data.state}): ${data.status || data.state}`;
            
            if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
                clearInterval(interval);
                statusDiv.innerHTML += `<br>Result: <code>${JSON.stringify(data.result || data.status)}</code>`;
            }
        }, 3000); 
    }
    </script>
</body></html>
"""

# --- Routing ---
@app.route('/', methods=['GET'])
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/start_audit', methods=['POST'])
def start_audit():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL parameter missing"}), 400

    # Submit the task asynchronously
    task = run_full_audit.delay(url)
    
    return jsonify({
        "message": f"Audit started for {url}",
        "task_id": task.id
    }), 202 

@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = celery_app.AsyncResult(task_id)
    
    # ... Logic to check task status (PENDING, SUCCESS, FAILURE) ...
    response = {'state': task.state}
    if task.state == 'SUCCESS':
        response['result'] = task.result
        response['status'] = 'Completed successfully'
    elif task.state == 'FAILURE':
        response['status'] = str(task.info)
    else:
        response['status'] = 'Processing...'
        
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
