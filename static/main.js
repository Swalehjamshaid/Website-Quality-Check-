// static/main.js

document.addEventListener('DOMContentLoaded', () => {
    const auditForm = document.getElementById('auditForm');
    const urlInput = document.getElementById('urlInput');
    const statusMessage = document.getElementById('statusMessage');
    const resultsContainer = document.getElementById('resultsContainer');

    if (!auditForm) return;

    // Handle form submission
    auditForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = urlInput.value;
        if (!url) return;

        // Reset display and show status
        resultsContainer.innerHTML = '';
        statusMessage.textContent = 'Submitting audit request...';
        statusMessage.classList.remove('hidden', 'bg-red-100', 'text-red-700');
        statusMessage.classList.add('bg-indigo-100', 'text-indigo-700');

        try {
            // 1. Send URL to backend (mocked /audit route)
            const response = await fetch('/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });

            const data = await response.json();
            const taskId = data.task_id;

            if (response.status === 202) {
                // 2. Start polling for status updates
                pollTaskStatus(taskId, url);
            } else {
                statusMessage.textContent = `Error starting audit: ${data.error}`;
            }

        } catch (error) {
            statusMessage.textContent = `Network error: ${error.message}`;
            statusMessage.classList.replace('bg-indigo-100', 'bg-red-100');
            statusMessage.classList.replace('text-indigo-700', 'text-red-700');
        }
    });

    // Function to check task status repeatedly (mocked /status route)
    function pollTaskStatus(taskId, url) {
        let intervalId;

        const checkStatus = async () => {
            const statusResponse = await fetch(`/status/${taskId}`);
            const statusData = await statusResponse.json();

            // Update UI with progress
            statusMessage.textContent = `${statusData.status} (${statusData.progress}%)`;

            if (statusData.state === 'SUCCESS' || statusData.state === 'FAILURE') {
                clearInterval(intervalId); // Stop polling

                if (statusData.state === 'SUCCESS') {
                    statusMessage.textContent = `✅ Audit Complete! ID: ${statusData.audit_id}`;
                    
                    // Display mocked results on success
                    resultsContainer.innerHTML = `
                        <div class="result-card">
                            <h3 class="text-xl font-bold mb-2 text-gray-800">Mock Audit Results for: ${url}</h3>
                            <p class="text-gray-600 mb-4">Task ID: ${statusData.audit_id}</p>
                            <div class="space-y-2">
                                <div class="flex justify-between items-center border-b pb-1">
                                    <span class="font-semibold">HTTP Status Check:</span>
                                    <span class="status-pass">PASS (200 OK)</span>
                                </div>
                                <div class="flex justify-between items-center border-b pb-1">
                                    <span class="font-semibold">SEO Title Present:</span>
                                    <span class="status-pass">PASS</span>
                                </div>
                                <div class="flex justify-between items-center border-b pb-1">
                                    <span class="font-semibold">Overall Score:</span>
                                    <span class="text-2xl font-extrabold text-green-600">95/100</span>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    statusMessage.textContent = `❌ Audit Failed: ${statusData.status}`;
                    statusMessage.classList.replace('bg-indigo-100', 'bg-red-100');
                    statusMessage.classList.replace('text-indigo-700', 'text-red-700');
                }
            }
        };

        // Start checking every 3 seconds
        intervalId = setInterval(checkStatus, 3000);
    }
});
