# tasks/run_full_audit.py — FULL PROFESSIONAL AUDIT (100% Vercel Safe)
import requests
from bs4 import BeautifulSoup
import time

def run_full_audit_func(url: str) -> dict:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    start_time = time.time()
    score = 100
    details = {}
    warnings = []

    # 1. Fetch page
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; QualityCheckerBot/1.0)"}
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        load_time = time.time() - start_time
    except Exception as e:
        return {
            "url": url,
            "score": 10,
            "summary": "Website unreachable",
            "details": {"Error": str(e)},
            "warnings": ["Cannot connect to site"]
        }

    # 2. Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # HTTP & Security
    details["HTTPS"] = "PASS" if response.url.startswith("https://") else "FAIL"
    if not response.url.startswith("https://"): score -= 20

    details["Status Code"] = f"{response.status_code} OK" if response.status_code == 200 else f"{response.status_code} ERROR"
    if response.status_code != 200: score -= 50

    details["Load Time"] = f"{load_time:.2f}s"
    if load_time > 5: score -= 15; warnings.append("Very slow")
    elif load_time > 3: score -= 8

    # SEO Essentials
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""
    details["Page Title"] = "PASS" if title_text and 10 < len(title_text) < 70 else "FAIL"
    if not title_text or len(title_text) > 70 or len(title_text) < 10: score -= 20

    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""
    details["Meta Description"] = "PASS" if desc and 50 < len(desc) < 160 else "FAIL"
    if not desc or len(desc) > 160 or len(desc) < 50: score -= 15

    # Structure
    h1s = soup.find_all("h1")
    details["H1 Tags"] = f"PASS ({len(h1s)})" if 1 <= len(h1s) <= 3 else f"WARNING ({len(h1s)})"
    if len(h1s) == 0 or len(h1s) > 3: score -= 10

    # Images
    imgs = soup.find_all("img")
    no_alt = [img for img in imgs if not img.get("alt") or img.get("alt").strip() == ""]
    details["Image Alt Text"] = f"PASS (all {len(imgs)} have alt)" if not no_alt else f"FAIL ({len(no_alt)} missing)"
    if no_alt: score -= min(len(no_alt) * 4, 20)

    # Mobile
    viewport = soup.find("meta", attrs={"name": "viewport"})
    details["Mobile Friendly"] = "PASS" if viewport else "FAIL"
    if not viewport: score -= 15

    # Favicon
    favicon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
    details["Favicon"] = "PASS" if favicon else "FAIL"
    if not favicon: score -= 5

    final_score = max(score, 0)

    return {
        "url": url,
        "score": final_score,
        "summary": f"Website Quality Score: {final_score}/100",
        "details": details,
        "warnings": warnings,
        "load_time": round(load_time, 2)
    }
