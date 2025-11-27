import random
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from math import ceil
from typing import List, Dict, Any

# --- FastAPI and Pydantic Imports ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
# CRITICAL: The app instance must be named 'app' for Vercel to find it.
app = FastAPI(title="QA Autopilot API", version="1.0")


# --- Configuration for CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your Vercel frontend to call this API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Data Models ---

class ClientInput(BaseModel):
    client_id: str
    website_url: str

class FullReport(BaseModel):
    id: str
    website_url: str
    health_score: int
    summary: Dict[str, int]
    issues_found: List[str]
    details: Dict[str, Any]
    timestamp: str


# --- Core QA Logic (Real Checks + Mock Data) ---

def random_score(min_val, max_val):
    return random.randint(min_val, max_val)

def perform_basic_scrape_and_checks(url: str) -> Dict[str, Any]:
    """Performs a simple scrape and basic SEO/Health checks."""
    issues = []
    try:
        # Use a header to mimic a browser
        headers = {'User-Agent': 'Mozilla/5.0 (Vercel-QA-Bot)'}
        response = requests.get(url, timeout=10, headers=headers)
        http_status = response.status_code
        status_score = 100 if http_status == 200 else 40
        if http_status != 200:
            issues.append(f"Critical: HTTP Status is {http_status}. Page is not fully accessible.")

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check Title Tag
        title = soup.find('title').text if soup.find('title') else 'N/A'
        title_tag_check = 'good' if len(title) > 10 and len(title) < 70 else 'warn'
        if title_tag_check == 'warn':
             issues.append("SEO Warning: Title tag is missing or poorly optimized.")

        # Check H1 Tag
        h1_count = len(soup.find_all('h1'))
        h1_tag_check = 'good' if h1_count == 1 else 'warn'
        if h1_count != 1:
            issues.append(f"SEO Warning: Found {h1_count} H1 tags (should be 1).")
            
    except requests.exceptions.RequestException as e:
        issues.append(f"Critical Error: Could not reach the URL. Details: {e}")
        status_score = 10 
        http_status = 0
        h1_count = 0
        title = 'N/A'
        title_tag_check = 'critical'
        h1_tag_check = 'critical'

    return {
        'issues': issues, 'http_status': http_status, 'title': title, 
        'h1_count': h1_count, 'status_score': status_score, 
        'title_tag_check': title_tag_check, 'h1_tag_check': h1_tag_check,
    }


def generate_report_python(url: str) -> Dict[str, Any]:
    check_results = perform_basic_scrape_and_checks(url)
    
    # Generate scores (mixing real check with random data)
    perf_score = random_score(40, 95)
    seo_score = ceil((random_score(60, 100) + check_results['status_score']) / 2)
    security_score = random_score(70, 98)
    mobile_score = random_score(50, 99)
    link_score = random_score(80, 100)
    
    health_score = ceil((perf_score * 0.25 + seo_score * 0.2 + security_score * 0.2 + mobile_score * 0.15 + link_score * 0.2))

    # Compile issues
    potential_issues = check_results['issues']
    if perf_score < 70: potential_issues.append('Large image files detected.')
    if security_score < 85: potential_issues.append('Missing crucial security headers (CSP).')
    
    issues_found = random.sample(potential_issues, min(random_score(1, 4), len(potential_issues))) if potential_issues else []

    detailed_report_data = {
        'performance': {
            'score': perf_score,
            'metrics': [
                {'name': 'HTTP Status Code', 'value': check_results['http_status'], 'status': 'critical' if check_results['http_status'] != 200 else 'good'},
                {'name': 'FCP (Simulated)', 'value': f'{random_score(1, 3)}s', 'status': 'slow' if perf_score < 70 else 'good'},
            ],
        },
        'seo': {
            'score': seo_score,
            'metrics': [
                {'name': 'Title Tag Content', 'value': check_results['title'], 'status': check_results['title_tag_check']},
                {'name': 'H1 Tag Count', 'value': check_results['h1_count'], 'status': check_results['h1_tag_check']},
            ],
        },
        'security': {
             'score': security_score, 
             'metrics': [{'name': 'SSL/TLS Status', 'value': 'Active', 'status': 'good'}]
        },
        'mobile': {
             'score': mobile_score, 
             'metrics': [{'name': 'Viewport Tag', 'value': 'Present', 'status': 'good'}]
        },
        'links': {
             'score': link_score, 
             'metrics': [{'name': 'Broken Internal Links', 'value': '0', 'status': 'good'}]
        }
    }

    temp_id = f"{url.split('//')[-1].split('/')[0]}_{int(time.time())}"

    return {
        'id': temp_id, 'timestamp': datetime.now().isoformat(), 'website_url': url,
        'health_score': health_score,
        'summary': {
            'performance': perf_score, 'seo': seo_score, 'security': security_score, 'mobile': mobile_score, 'links': link_score,
        },
        'issues_found': issues_found,
        'details': detailed_report_data,
    }


# --- API Endpoints ---

@app.get("/")
def read_root():
    """Temporary root endpoint to ensure the Vercel Serverless Function starts successfully."""
    return {"status": "ok", "message": "QA API Server is active"}

@app.post("/api/run_qa_test", response_model=FullReport)
async def run_qa_test_api(client_data: ClientInput):
    """Handles POST requests to run the QA test."""
    if not client_data.website_url.startswith(('http://', 'https://')):
        client_data.website_url = 'https://' + client_data.website_url
        
    time.sleep(random_score(3, 5)) # Simulate latency
    
    try:
        report_data = generate_report_python(client_data.website_url)
    except Exception as e:
        # Raise an HTTPException on failure
        raise HTTPException(status_code=500, detail=f"Analysis failed due to a server error: {e}")
    
    return report_data
