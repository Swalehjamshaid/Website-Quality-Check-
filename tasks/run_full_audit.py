# tasks/run_full_audit.py
from celery import shared_task
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
from tasks.reporting.report_generator import generate_pdf_report

@shared_task(bind=True)
def run_full_audit(self, url):
    if not url.startswith("http"):
        url = "https://" + url
    
    results = {
        "url": url,
        "score": 0,
        "checks": {},
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Website Quality Checker Bot)'}
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Basic Checks
        results["checks"]["HTTP Status"] = f"PASS (200 OK)"
        results["checks"]["Title"] = "PASS" if soup.title and soup.title.string else "FAIL (Missing)"
        results["checks"]["Meta Description"] = "PASS" if soup.find("meta", attrs={"name": "description"}) else "FAIL"
        results["checks"]["H1 Tag"] = "PASS" if soup.find("h1") else "FAIL (Missing)"
        results["checks"]["Viewport Meta"] = "PASS" if soup.find("meta", attrs={"name": "viewport"}) else "FAIL"
        results["checks"]["Canonical Tag"] = "PASS" if soup.find("link", rel="canonical") else "WARNING"

        # Count images without alt
        img_no_alt = len([img for img in soup.find_all("img") if not img.get("alt")])
        results["checks"]["Images without alt"] = f"{img_no_alt} found"

        # Simple scoring
        passed = sum(1 for v in results["checks"].values() if "PASS" in str(v))
        total = len(results["checks"])
        results["score"] = round((passed / total) * 100, 1)

        results["score"] = round((passed / total) * 100, 1)

        # Generate PDF
        pdf_path = generate_pdf_report(results)
        results["report_url"] = f"/reports/{os.path.basename(pdf_path)}"

    except Exception as e:
        results["checks"]["Error"] = str(e)
        results["score"] = 0

    # Update progress (optional)
    self.update_state(state='PROGRESS', meta={'progress': 100})

    return results
