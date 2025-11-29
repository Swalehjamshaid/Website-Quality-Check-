import requests
from bs4 import BeautifulSoup
import time

# ONLY THIS NAME — run_full_audit_func
def run_full_audit_func(url):
    if not url.startswith("http"):
        url = "https://" + url

    try:
        start = time.time()
        r = requests.get(url, timeout=15, allow_redirects=True)
        load_time = time.time() - start
    except:
        return {"url": url, "score": 0, "summary": "Unreachable"}

    soup = BeautifulSoup(r.text, "html.parser")
    score = 100

    if r.status_code != 200: score -= 50
    if not r.url.startswith("https://"): score -= 20
    if not soup.title or not soup.title.string: score -= 20
    if load_time > 3: score -= 10

    return {
        "url": url,
        "score": max(score, 0),
        "summary": f"Score: {max(score, 0)}/100",
        "details": {
            "Status": r.status_code,
            "HTTPS": "Yes" if r.url.startswith("https://") else "No",
            "Load Time": f"{load_time:.2f}s"
        }
    }
