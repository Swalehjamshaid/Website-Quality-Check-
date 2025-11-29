# tasks/tasks.py (REPLACES tasks/run_full_audit.py)

# Import the centralized Celery app instance (non-circular)
from .celery_app import celery_app 

# The name argument ensures that the task is still registered as 'run_full_audit', 
# matching your application logic, even though the file is named tasks.py.
@celery_app.task(name='run_full_audit') 
def run_full_audit(url: str):
    """
    The main background function that performs the quality audit.
    """
    # Placeholder for the actual long-running audit logic
    import time
    time.sleep(5) 
    
    if "error" in url.lower():
        raise Exception(f"Audit failed for {url}: Encountered a server issue.")
    
    return {
        "url": url,
        "status": "SUCCESS",
        "score": 98,
        "details": "All checks passed."
    }
