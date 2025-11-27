import random
from datetime import datetime
from math import ceil
import json
import time

# --- FastAPI and Pydantic Imports ---
# Make sure these are in your requirements.txt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


# --- Pydantic Data Models for API ---

class ClientInput(BaseModel):
    """Expected input from the React front-end."""
    client_id: str
    website_url: str

class FullReport(BaseModel):
    """The full report structure returned to the React front-end."""
    id: str
    website_url: str
    health_score: int
    summary: dict
    issues_found: list[str]
    details: dict
    timestamp: str


# --- FastAPI Initialization ---

app = FastAPI(title="QA Autopilot Backend API", version="1.0")

# CRITICAL: Configure CORS to allow your Vercel/React frontend to call this API.
# WARNING: For production, replace allow_origins=["*"] with your specific Vercel URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Core QA Logic ---

def random_score(min_val, max_val):
    """Generates a random score between min_val and max_val (inclusive)."""
    return random.randint(min_val, max_val)

def generate_report_python(url):
    """Generates a full report dictionary, matching the structure expected by the React frontend."""
    
    # Generate scores for each category
    perf_score = random_score(40, 95)
    seo_score = random_score(60, 100)
    security_score = random_score(70, 98)
    mobile_score = random_score(50, 99)
    link_score = random_score(80, 100)

    # Calculate overall health score (weighted average)
    health_score = ceil((perf_score * 0.25 + seo_score * 0.2 + security_score * 0.2 + mobile_score * 0.15 + link_score * 0.2))

    issues = [
        'Missing H1 tag on homepage',
        'Image sizes are too large (1.5MB+)',
        'Server response time is slow (> 500ms)',
        'CORS policy detected on payment gateway',
        'Broken internal link on the "About Us" page',
        'Viewports are not optimized for tablets',
        'Missing Security Headers (CSP)',
    ]
    
    # --- DETAILED REPORT STRUCTURE (must match React index.html exactly) ---
    detailed_report = {
        'performance': {
            'score': perf_score,
            'metrics': [
                {'name': 'FCP (First Contentful Paint)', 'value': f'{random_score(1, 3)}s', 'status': 'slow' if perf_score < 70 else 'good'},
                {'name': 'Server Response Time', 'value': f'{random_score(100, 800)}ms', 'status': 'slow' if perf_score < 60 else 'ok'},
                {'name': 'Render Blocking Resources', 'value': str(random_score(0, 5)), 'status': 'warn' if perf_score < 80 else 'good'},
            ],
        },
        'seo': {
            'score': seo_score,
            'metrics': [
                {'name': 'Meta Descriptions', 'value': f'{random_score(90, 100)}% coverage', 'status': 'warn' if seo_score < 90 else 'good'},
                {'name': 'Canonical Tags', 'value': f'{random_score(95, 100)}% present', 'status': 'ok' if seo_score > 95 else 'good'},
                {'name': 'H1 Tag Check', 'value': f'{random_score(70, 100)}% pass', 'status': 'warn' if seo_score < 85 else 'good'},
            ],
        },
        'security': {
            'score': security_score,
            'metrics': [
                {'name': 'SSL/TLS Status', 'value': 'Active', 'status': 'good'},
                {'name': 'Security Headers', 'value': 'Missing CSP' if security_score < 85 else 'All present', 'status': 'critical' if security_score < 85 else 'good'},
                {'name': 'Vulnerability Scan', 'value': 'None Found' if security_score > 95 else 'Low Severity', 'status': 'good' if security_score > 95 else 'warn'},
            ],
        },
        'mobile': {
            'score': mobile_score,
            'metrics': [
                {'name': 'Tap Target Size', 'value': 'Good' if mobile_score > 90 else 'Needs Fix', 'status': 'good' if mobile_score > 90 else 'warn'},
                {'name': 'Viewport Tag', 'value': 'Present', 'status': 'good'},
            ],
        },
        'links': {
            'score': link_score,
            'metrics': [
                {'name': 'Broken Internal Links', 'value': '0' if link_score > 98 else str(random_score(1, 5)), 'status': 'critical' if link_score < 98 else 'good'},
                {'name': 'Broken External Links', 'value': '0', 'status': 'good'},
            ],
        }
    }

    # Add a few issues based on scores
    potential_issues = []
    if perf_score < 70: potential_issues.extend([issues[1], issues[2]])
    if seo_score < 80: potential_issues.append(issues[0])
    if security_score < 85: potential_issues.extend([issues[3], issues[6]])
    if mobile_score < 80: potential_issues.append(issues[5])
    if link_score < 95: potential_issues.append(issues[4])
    
    issues_found = random.sample(potential_issues, min(random_score(1, 4), len(potential_issues))) if potential_issues else []

    # Generate a temporary ID (React will use the Client ID for the report if needed, or generate its own UUID)
    temp_id = f"{url.split('//')[-1].split('/')[0]}_{int(time.time())}"

    return {
        'id': temp_id, 
        'timestamp': datetime.now().isoformat(),
        'website_url': url,
        'health_score': health_score,
        'summary': {
            'performance': perf_score,
            'seo': seo_score,
            'security': security_score,
            'mobile': mobile_score,
            'links': link_score,
        },
        'issues_found': issues_found,
        'details': detailed_report,
    }


# --- API Endpoint ---

@app.post("/api/run_qa_test", response_model=FullReport)
async def run_qa_test_api(client_data: ClientInput):
    """
    Receives a website URL from the React front-end, runs the mock QA analysis, 
    and returns the structured report data.
    """
    # Simulate the latency of a real test (3-5 seconds)
    time.sleep(random_score(3, 5))
    
    report_data = generate_report_python(client_data.website_url)
    
    return report_data


@app.get("/health")
def health_check():
    """Simple endpoint to verify the API is running."""
    return {"status": "ok", "message": "QA Autopilot API is operational"}


# --- Uvicorn Server Command (for local testing/deployment) ---

if __name__ == "__main__":
    import uvicorn
    # To run locally, save as qa_api.py and execute: python -m uvicorn qa_api:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
