# tasks/run_full_audit.py — FULL PROFESSIONAL AUDIT (100% works on Vercel)
import requests
from bs4 import BeautifulSoup
import time
import ssl
import socket

def run_full_audit_func(url: str) -> dict:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    start_time = time.time()
    score = 100
    details = {}
    warnings = []

    # 1. HTTP Request
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; WebsiteQualityChecker/2.0)"
        }
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True, verify=True)
        load_time = time.time() - start_time
    except Exception as e:
        return {
            "url": url,
            "score": 10,
            "summary": "Website is down or unreachable",
            "details": {"Error": str(e)},
            "warnings": []
        }

    # 2. Basic Checks
    details["HTTP Status"] = f"PASS (200 OK)" if response.status_code == 200 else f"FAIL ({response.status_code})"
    if response.status_code != 200:
        score -= 50

    details["Load Time"] = f"{load_time:.2f}s"
    if load_time > 5:
        score -= 15
        warnings.append("Very slow loading")
    elif load_time > 3:
        score -= 8

    details["SSL Certificate"] = "PASS" if response.url.startswith("https://") else "FAIL (No HTTPS)"
    if not response.url.startswith("https://"):
        score -= 20

    # 3. HTML Parsing
    soup = BeautifulSoup(response.text, "html.parser")

    # Title
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""
    details["Page Title"] = "PASS" if title_text and len(title_text) > 10 else "FAIL"
    if not title_text or len(title_text) < 10:
        score -= 20

    # Meta Description
    meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    desc_text = meta_desc.get("content", "") if meta_desc else ""
    details["Meta Description"] = "PASS" if desc_text and len(desc_text) > 50 else "FAIL"
    if not desc_text or len(desc_text) < 50:
        score -= 15

    # Headings
    h1_count = len(soup.find_all("h1"))
    details["H1 Tags"] = f"PASS ({h1_count})" if 1 <= h1_count <= 3 else f"WARNING ({h1_count})"
    if h1_count == 0 or h1_count > 3:
        score -= 10

    # Images without alt
    bad_imgs = [img for img in soup.find_all("img") if not img.get("alt") or img.get("alt").strip() == ""]
    details["Images with Alt Text"] = f"PASS ({len(bad_imgs)} missing)" if len(bad_imgs) == 0 else f"FAIL ({len(bad_imgs)} missing)"
    if bad_imgs:
        score -= len(bad_imgs) * 3
        warnings.append(f"{len(bad_imgs)} images missing alt text")

    # Mobile Friendly (viewport)
    viewport = soup.find("meta", attrs={"name": "viewport"})
    details["Mobile Friendly"] = "PASS" if viewport else "FAIL"
    if not viewport:
        score -= 15

    # Favicon
    favicon = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
    details["Favicon"] = "PASS" if favicon else "FAIL"
    if not favicon:
        score -= 5

    final_score = max(score, 0)

    return {
        "url": url,
        "score": final_score,
        "summary": "Audit completed",
        "details": details,
        "warnings": warnings,
        "load_time": round(load_time, 2)
    }
