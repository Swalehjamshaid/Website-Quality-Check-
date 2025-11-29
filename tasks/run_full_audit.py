from app import celery, supabase
import requests
from bs4 import BeautifulSoup
import time
import uuid
from datetime import datetime

@celery.task(bind=True)
def run_full_audit(self, url):
    """
    Performs a comprehensive quality check on the given URL.
    """
    self.update_state(state='PENDING', meta={'url': url, 'progress': 0, 'status': 'Starting audit...'})
    
    # --- Check 1: HTTP Status and Response Time ---
    try:
        self.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'Checking HTTP status...'})
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = round(time.time() - start_time, 2)
        status_code = response.status_code
        
        http_check = {
            'status': 'PASS' if 200 <= status_code < 300 else 'FAIL',
            'status_code': status_code,
            'response_time': response_time
        }
    except requests.exceptions.RequestException as e:
        http_check = {'status': 'FAIL', 'error': str(e)}
        status_code = 500
        
    # --- Check 2: Basic SEO Tags ---
    seo_check = {'status': 'N/A'}
    
    if http_check['status'] == 'PASS':
        self.update_state(state='PROGRESS', meta={'progress': 50, 'status': 'Checking SEO tags...'})
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('title')
        description = soup.find('meta', attrs={'name': 'description'})
        
        seo_status = 'PASS'
        if not title or len(title.string.strip()) < 5:
            seo_status = 'FAIL'
        
        seo_check = {
            'status': seo_status,
            'title_present': bool(title),
            'desc_present': bool(description)
        }

    # --- 3. Compile Raw Results ---
    audit_id = str(uuid.uuid4())
    raw_results = {
        'audit_id': audit_id,
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'http_status': http_check,
        'seo_tags': seo_check
    }
    
    # --- 4. Save Raw Results ---
    self.update_state(state='PROGRESS', meta={'progress': 80, 'status': 'Saving results...'})
    
    try:
        supabase.table('audits').insert(raw_results).execute()
        
    except Exception as e:
        print(f"Supabase error: {e}")
        
    return {'progress': 100, 'status': 'Audit Complete', 'audit_id': audit_id}
