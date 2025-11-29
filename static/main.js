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

        // Reset display
        resultsContainer.innerHTML = '';
        statusMessage.textContent = 'Submitting audit request...';
        statusMessage.classList.remove('hidden');

        try {
            // 1. Send URL to backend to start the audit
            const response = await fetch('/audit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
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
        }
    });

    // Function to check task status repeatedly
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
                    resultsContainer.innerHTML = `
                        <h3 class="text-xl font-bold mt-4">Results Summary for ${url}</h3>
                        <p>Detailed results would be fetched here using the Audit ID: ${statusData.audit_id}</p>
                    `;
                    // NOTE: In a real app, you'd make an API call to fetch the final report data.
                } else {
                    statusMessage.textContent = `❌ Audit Failed: ${statusData.status}`;
                }
            }
        };

        // Start checking every 3 seconds
        intervalId = setInterval(checkStatus, 3000);
    }
});
