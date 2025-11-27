import random
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from math import ceil

# --- FastAPI and Pydantic Imports ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

# --- Pydantic Data Models for API ---

class ClientInput(BaseModel):
    """Expected input from the React front-end."""
    client_id: str
    website_url: str

class Metric(BaseModel):
    name: str
    value: Any
    status: str

class CategoryDetail(BaseModel):
    score: int
    metrics: List[Metric]

class DetailedReport(BaseModel):
    performance: CategoryDetail
    seo: CategoryDetail
    security: CategoryDetail
    mobile: CategoryDetail
    links: CategoryDetail

class FullReport(BaseModel):
    """The full report structure returned to the front-end."""
    id: str
    website_url: str
    health_score: int
    summary: Dict[str, int]
    issues_found: List[str]
    details: DetailedReport
    timestamp: str


# --- FastAPI Initialization ---

app = FastAPI(
    title="QA Autopilot Backend API",
    version="1.0",
    description="A Website Quality Audit Mock API with real-world basic checks."
)

# CRITICAL: Configure CORS to allow your frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local testing. Replace with your domain in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Core QA Logic (Basic Real Checks + Mock Data) ---

def random_score(min_val, max_val):
    """Generates a random score between min_val and max_val (inclusive)."""
    return random.randint(min_val, max_val)

def perform_basic_scrape_and_checks(url: str) -> Dict[str, Any]:
    """Performs a simple scrape and basic SEO/Health checks."""
    issues = []
    
    try:
        # 1. HTTP Status Check
        response = requests.get(url, timeout=10)
        http_status = response.status_code
        if http_status != 200:
            issues.append(f"Critical: HTTP Status is {http_status}. Page is not fully accessible.")
            status_score = 40
        else:
            status_score = 100
        
        # 2. Scrape for SEO Elements
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check Title Tag
        title = soup.find('title').text if soup.find('title') else 'N/A'
        title_tag_check = 'good'
        if title == 'N/A' or len(title) < 10 or len(title) > 70:
            issues.append("SEO Warning: Title tag is missing or poorly optimized.")
            title_tag_check = 'warn'

        # Check H1 Tag
        h1_tags = soup.find_all('h1')
        h1_count = len(h1_tags)
        h1_tag_check = 'good'
        if h1_count == 0:
            issues.append("SEO Warning: Missing H1 tag on the page.")
            h1_tag_check = 'warn'
        elif h1_count > 1:
            issues.append(f"SEO Warning: Found {h1_count} H1 tags (only one is recommended).")
            h1_tag_check = 'warn'
        
    except requests.exceptions.RequestException as e:
        issues.append(f"Critical Error: Could not reach the URL. Details: {e}")
        http_status = 0
        title = 'N/A'
        h1_count = 0
        status_score = 10 # Lowest possible score on connection failure
        title_tag_check = 'critical'
        h1_tag_check = 'critical'


    return {
        'issues': issues,
        'http_status': http_status,
        'title': title,
        'h1_count': h1_count,
        'status_score': status_score,
        'title_tag_check': title_tag_check,
        'h1_tag_check': h1_tag_check,
    }


def generate_report_python(url: str) -> Dict[str, Any]:
    """Generates a full report dictionary, combining real checks with mock data."""
    
    # Run the real-world checks
    check_results = perform_basic_scrape_and_checks(url)
    
    # Generate mock scores for categories not yet implemented
    perf_score = random_score(40, 95)
    seo_score = ceil((random_score(60, 100) + check_results['status_score']) / 2) # Weighted by real status
    security_score = random_score(70, 98)
    mobile_score = random_score(50, 99)
    link_score = random_score(80, 100)

    # Calculate overall health score (weighted average)
    health_score = ceil((perf_score * 0.25 + seo_score * 0.2 + security_score * 0.2 + mobile_score * 0.15 + link_score * 0.2))

    # Compile mock issues (to fill out the report)
    mock_issues = [
        'Image sizes are too large (1.5MB+)',
        'Server response time is slow (> 500ms)',
        'CORS policy detected on payment gateway',
        'Viewports are not optimized for tablets',
        'Missing Security Headers (CSP)',
    ]
    
    # Combine real issues with a selection of mock issues
    potential_issues = check_results['issues']
    if perf_score < 70: potential_issues.extend([mock_issues[0], mock_issues[1]])
    if security_score < 85: potential_issues.extend([mock_issues[2], mock_issues[4]])
    if mobile_score < 80: potential_issues.append(mock_issues[3])
    if link_score < 95: potential_issues.append("Broken internal link on a deep page")
    
    issues_found = random.sample(potential_issues, min(random_score(1, 4), len(potential_issues))) if potential_issues else []

    # --- DETAILED REPORT STRUCTURE ---
    detailed_report_data = {
        'performance': {
            'score': perf_score,
            'metrics': [
                {'name': 'HTTP Status Code', 'value': check_results['http_status'], 'status': 'critical' if check_results['http_status'] != 200 else 'good'},
                {'name': 'FCP (First Contentful Paint)', 'value': f'{random_score(1, 3)}s', 'status': 'slow' if perf_score < 70 else 'good'},
            ],
        },
        'seo': {
            'score': seo_score,
            'metrics': [
                {'name': 'Title Tag Content', 'value': check_results['title'], 'status': check_results['title_tag_check']},
                {'name': 'H1 Tag Count', 'value': check_results['h1_count'], 'status': check_results['h1_tag_check']},
                {'name': 'Robots.txt Presence', 'value': 'Present', 'status': 'good'},
            ],
        },
        'security': {
            'score': security_score,
            'metrics': [
                {'name': 'SSL/TLS Status', 'value': 'Active', 'status': 'good'},
                {'name': 'Security Headers', 'value': 'Missing CSP' if security_score < 85 else 'All present', 'status': 'critical' if security_score < 85 else 'good'},
            ],
        },
        'mobile': {
            'score': mobile_score,
            'metrics': [
                {'name': 'Viewport Tag', 'value': 'Present', 'status': 'good'},
                {'name': 'Tap Target Size', 'value': 'Good' if mobile_score > 90 else 'Needs Fix', 'status': 'good' if mobile_score > 90 else 'warn'},
            ],
        },
        'links': {
            'score': link_score,
            'metrics': [
                {'name': 'Broken Internal Links', 'value': '0' if link_score > 98 else str(random_score(1, 5)), 'status': 'critical' if link_score < 98 else 'good'},
                {'name': 'External Link Check', 'value': 'Pass', 'status': 'good'},
            ],
        }
    }

    temp_id = f"{url.split('//')[-1].split('/')[0]}_{int(time.time())}"

    return {
        'id': temp_id, 
        'timestamp': datetime.now().isoformat(),
        'website_url': url,
        'health_score': health_score,
        'summary': {
            'performance': detailed_report_data['performance']['score'],
            'seo': detailed_report_data['seo']['score'],
            'security': detailed_report_data['security']['score'],
            'mobile': detailed_report_data['mobile']['score'],
            'links': detailed_report_data['links']['score'],
        },
        'issues_found': issues_found,
        'details': detailed_report_data,
    }


# --- API Endpoint ---

@app.post("/api/run_qa_test", response_model=FullReport)
async def run_qa_test_api(client_data: ClientInput):
    """
    Receives a website URL, runs the QA analysis, and returns the structured report data.
    """
    if not client_data.website_url.startswith(('http://', 'https://')):
        client_data.website_url = 'https://' + client_data.website_url
        
    # Simulate the latency of a real test (3-5 seconds)
    time.sleep(random_score(3, 5))
    
    try:
        report_data = generate_report_python(client_data.website_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    
    return report_data


@app.get("/health")
def health_check():
    """Simple endpoint to verify the API is running."""
    return {"status": "ok", "message": "QA Autopilot API is operational"}


# --- Uvicorn Server Command ---
# To run this API:
# 1. Install dependencies: pip install fastapi uvicorn 'pydantic[standard]' requests beautifulsoup4
# 2. Save the code as qa_api.py
# 3. Run: uvicorn qa_api:app --reload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
