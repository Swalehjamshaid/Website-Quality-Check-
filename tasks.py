# tasks.py
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from .app import celery, supabase # Import initialized components

# --- Lighthouse API Configuration ---
LIGHTHOUSE_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

def run_lighthouse_audit(url):
    """Performs the Lighthouse audit via Google PageSpeed Insights API."""
    params = {
        'url': url,
        'category': ['PERFORMANCE', 'SEO', 'ACCESSIBILITY'],
        'strategy': 'mobile' 
    }
    response = requests.get(LIGHTHOUSE_API_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    scores = {
        'performance_score': int(data['lighthouseResult']['categories']['performance']['score'] * 100),
        'seo_score': int(data['lighthouseResult']['categories']['seo']['score'] * 100),
        'accessibility_score': int(data['lighthouseResult']['categories']['accessibility']['score'] * 100)
    }
    return scores, data

def run_custom_crawler(url):
    """Custom crawler to check basic technical issues (links, tags)."""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Basic Broken Links Check 
        broken_links_count = 0
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Only checking external links for demonstration
            if href.startswith('http') and requests.head(href, timeout=5).status_code >= 400:
                broken_links_count += 1
        
        # Check SEO Tags
        title = soup.find('title').text if soup.find('title') else 'Title Missing'
        h1 = soup.find('h1').text if soup.find('h1') else 'H1 Missing'
        
        return {
            'broken_links_count': broken_links_count,
            'page_title': title,
            'h1_tag': h1,
            'status_code': response.status_code
        }
    except Exception as e:
        return {'error': str(e), 'status_code': 0}

@celery.task(bind=True)
def run_full_audit(self, website_id):
    """The main audit task: runs checks and saves results to Supabase."""
    
    # 1. Fetch Website URL
    website_data = supabase.table("websites").select("url").eq("id", website_id).execute().data
    if not website_data:
        return f"Website ID {website_id} not found."
    url = website_data[0]['url']

    try:
        # 2. Run Audit Components
        lighthouse_scores, lighthouse_data = run_lighthouse_audit(url)
        crawler_data = run_custom_crawler(url)
        
        # 3. Calculate Final Score 
        final_score = (lighthouse_scores['performance_score'] + lighthouse_scores['seo_score'] + lighthouse_scores['accessibility_score']) / 3
        
        full_raw_data = {
            'lighthouse_scores': lighthouse_scores,
            'crawler_data': crawler_data,
            'final_score': final_score,
        }

        # 4. Save Results to Supabase 'audit_results' table
        supabase.table("audit_results").insert({
            "website_id": website_id,
            "timestamp": datetime.now().isoformat(),
            "performance_score": lighthouse_scores['performance_score'],
            "seo_score": lighthouse_scores['seo_score'],
            # Store the combined data as a JSON string
            "raw_data": json.dumps(full_raw_data) 
        }).execute()

        return f"Audit for {url} completed. Score: {final_score:.0f}"

    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc': str(e)})
        return f"Audit failed for {url}: {str(e)}"
