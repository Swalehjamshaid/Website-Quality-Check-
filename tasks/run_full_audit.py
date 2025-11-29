# tasks/run_full_audit.py — FINAL CLEAN VERSION (NO IMPORT OF ITSELF)
import requests
from bs4 import BeautifulSoup
import time

def run_full_audit_func(url: str) -> dict:
    if not url.startswith("http"):
        url = "https://" + url

    start = time.time()
    score = 100
    details = {}

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        load_time = time.time() - start
    except:
        return {"url": url, "score": 0, "summary": "Site down", "details": {"Error": "Cannot reach website"}}

    soup = BeautifulSoup(r.text, "html.parser")

    # Real checks
    details["Status"] = "PASS (200)" if r.status_code == 200 else f"FAIL ({r.status_code})"
    if r.status_code != 200: score -= 50

    details["HTTPS"] = "PASS" if r.url.startswith("https://") else "FAIL"
    if not r.url.startswith("https://"): score -= 20

    title = soup.title.string if soup.title else ""
    details["Title"] = "PASS" if title and len(title) > 10 else "FAIL"
    if not title or len(title) < 10: score -= 20

    desc = soup.find("meta", attrs={"name": "description"})
    details["Meta Desc"] = "PASS" if desc and desc.get("content") else "FAIL"
    if not desc: score -= 15

    details["Load Time"] = f"{load_time:.2f}s"
    if load_time > 3: score -= 10

    return {
        "url": url,
        "score": max(score, 0),
        "summary": f"Quality Score: {max(score, 0)}/100",
        "details": details
    }
