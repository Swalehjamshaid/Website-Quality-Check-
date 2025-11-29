# tasks/tasks.py

# Import the centralized Celery app instance from the same package
from .celery_app import celery_app 

# We use the name argument to match the task name in your original error, 
# even though the file name is 'tasks.py'.
@celery_app.task(name='run_full_audit') 
def run_full_audit(url: str):
    """
    The main background function that performs the quality audit.
    """
    print(f"--- [TASK START] Starting audit for URL: {url} ---")
    
    # 1. Simulate the work
    import time
    time.sleep(5) # The actual audit (network requests, parsing, scoring) happens here
    
    # 2. Add logic to handle different outcomes
    if "error" in url.lower():
        # Example of a failed audit
        raise Exception(f"Audit failed for {url}: Critical server error detected.")
    
    # 3. Return the result (Celery stores this result in the backend)
    result_data = {
        "url": url,
        "status": "SUCCESS",
        "score": 95,
        "details": "All critical checks passed."
    }
    
    print(f"--- [TASK END] Audit finished for URL: {url} ---")
    return result_data
