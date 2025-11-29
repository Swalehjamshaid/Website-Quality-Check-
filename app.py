# tasks/run_full_audit.py — 100% Vercel compatible
import requests
from bs4 import BeautifulSoup
import time

def run_full_audit_func(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return {
            "url": url,
            "score": 10,
            "summary": "Website unreachable",
            "details": {"HTTP Status": f"FAIL – {str(e)}"}
        }

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find("title")
    meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})

    score = 100
    details = {}

    # HTTP Status
    if response.status_code == 200:
        details["HTTP Status"] = "PASS (200 OK)"
    else:
        details["HTTP Status"] = f"FAIL ({response.status_code})"
        score -= 40

    # Title
    if title and len(title.get_text(strip=True)) > 10:
        details["SEO Title Present"] = "PASS"
    else:
        details["SEO Title Present"] = "FAIL (missing or too short)"
        score -= 25

    # Meta Description
    if meta_desc and len(meta_desc.get("content", "")) > 50:
        details["Meta Description"] = "PASS"
    else:
        details["Meta Description"] = "FAIL (missing or too short)"
        score -= 20

    # Response time
    load_time = response.elapsed.total_seconds()
    if load_time < 3:
        details["Load Time"] = f"PASS ({load_time:.2f}s)"
    else:
        details["Load Time"] = f"SLOW ({load_time:.2f}s)"
        score -= 10

    return {
        "url": url,
        "score": max(score, 0),
        "summary": "Audit completed",
        "details": details
    }
