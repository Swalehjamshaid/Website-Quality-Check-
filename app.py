# app.py

from flask import Flask, render_template_string, request, jsonify
# 1. Import the specific task function you want to run
from tasks.tasks import run_full_audit
# 2. Import the celery app instance (only needed to check results)
from tasks.celery_app import celery_app 


app = Flask(__name__)

# --- HTML Template for the Dashboard (Simplified for this example) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>Quality Check Dashboard</title></head>
<body>
    <h1>Quality Check Dashboard</h1>
    <p>Enter a URL to start a background audit.</p>
    <form method="POST" action="/start_audit">
        <input type="text" name="url" value="https://google.com" style="width: 300px;">
        <button type="submit" style="background-color: #6c5ce7; color: white;">Run Check</button>
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
            statusDiv.innerHTML = `Task started! ID: <b>${data.task_id}</b>. <a href="${data.status_url}" target="_blank">Check Status</a>`;
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
            
            statusDiv.innerHTML = `Status (${data.state}): ${JSON.stringify(data.status)}`;
            
            if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
                clearInterval(interval);
                statusDiv.innerHTML += `<br>Result: <code>${JSON.stringify(data.result || data.status)}</code>`;
            }
        }, 3000); // Poll every 3 seconds
    }
    </script>
</body>
</html>
"""

# --- Dashboard View ---
@app.route('/', methods=['GET'])
def index():
    return render_template_string(DASHBOARD_HTML)


# --- Task Submission Endpoint ---
@app.route('/start_audit', methods=['POST'])
def start_audit():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL parameter missing"}), 400

    try:
        # Call the task function using .delay() to execute it asynchronously
        task = run_full_audit.delay(url)
        
        response_data = {
            "message": f"Audit started successfully for {url}",
            "task_id": task.id,
            "status_url": f"/status/{task.id}"
        }
        
        # HTTP 202 Accepted status code is appropriate for background processing
        return jsonify(response_data), 202 
        
    except Exception as e:
        # Catch any errors during the task submission process itself
        return jsonify({"error": f"Error starting task: {str(e)}"}), 500


# --- Task Status Endpoint ---
@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Task is pending...'}
    elif task.state != 'FAILURE':
        response = {'state': task.state, 'status': 'Processing...'}
        if task.state == 'SUCCESS':
            response['result'] = task.result # The return value of run_full_audit()
            response['status'] = 'Completed successfully'
    else:
        # Task execution failed
        response = {
            'state': task.state,
            'status': str(task.info),  # exception details
            'result': 'Check server logs for details.'
        }
        
    return jsonify(response)


if __name__ == '__main__':
    # Flask runs on one port, Celery worker/broker runs separately
    app.run(debug=True, port=5000)
