# tasks/audit_engine.py — FINAL, CLEAN, PROFESSIONAL AUDIT (Works 100% on Vercel)
import requests
from bs4 import BeautifulSoup
import time

def perform_real_audit(url: str) -> dict:
    """Full real website quality audit — no mock, no errors"""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    start_time = time.time()

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        load_time = time.time() - start_time
    except Exception as e:
        return {
            "url": url,
            "score": 5,
            "summary": "Website is down or blocked",
            "details": {"Error": str(e)},
            "warnings": ["Could not connect"]
        }

    soup = BeautifulSoup(response.text, "html.parser")
    score = 100
    details = {}
    warnings = []

    # 1. Status Code
    details["Status Code"] = "PASS (200)" if response.status_code == 200 else f"FAIL ({response.status_code})"
    if response.status_code != 200:
        score -= 50

    # 2. HTTPS
    details["HTTPS"] = "PASS" if response.url.startswith("https://") else "FAIL"
    if not response.url.startswith("https://"):
        score -= 20

    # 3. Load Time
    details["Load Time"] = f"{load_time:.2f}s"
    if load_time > 5:
        score -= 15
        warnings.append("Very slow")
    elif load_time > 3:
        score -= 8

    # 4. Title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    details["Page Title"] = "PASS" if title and len(title) > 10 else "FAIL"
    if not title or len(title) < 10:
        score -= 20

    # 5. Meta Description
    meta = soup.find("meta", attrs={"name": "description"})
    desc = meta["content"].strip() if meta and meta.get("content") else ""
    details["Meta Description"] = "PASS" if desc and len(desc) > 50 else "FAIL"
    if not desc or len(desc) < 50:
        score -= 15

    # 6. Mobile Friendly
    viewport = soup.find("meta", attrs={"name": "viewport"})
    details["Mobile Friendly"] = "PASS" if viewport else "FAIL"
    if not viewport:
        score -= 15

    # 7. Images Alt Text
    imgs = soup.find_all("img")
    no_alt = [img for img in imgs if not img.get("alt") or img.get("alt").strip() == ""]
    details["Image Alt Text"] = f"PASS (all {len(imgs)})" if not no_alt else f"FAIL ({len(no_alt)} missing)"
    if no_alt:
        score -= min(len(no_alt) * 3, 20)

    final_score = max(score, 0)

    return {
        "url": url,
        "score": final_score,
        "summary": f"Website Quality Score: {final_score}/100",
        "details": details,
        "warnings": warnings,
        "load_time": round(load_time, 2)
    }
