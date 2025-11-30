import requests

def perform_real_audit(url):
    if not url.startswith("http"):
        url = "https://" + url

    API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    results = {"url": url, "desktop": {}, "mobile": {}}

    for strategy in ["desktop", "mobile"]:
        params = {
            "url": url,
            "strategy": strategy,
            "category": ["performance", "accessibility", "best-practices", "seo"]
        }
        try:
            res = requests.get(API, params=params, timeout=30)
            if res.status_code != 200:
                raise Exception(f"API failed: {res.text}")
            data = res.json()
            lr = data["lighthouseResult"]
            cat = lr["categories"]

            results[strategy] = {
                "performance": round(cat["performance"]["score"] * 100),
                "accessibility": round(cat["accessibility"]["score"] * 100),
                "best_practices": round(cat["best-practices"]["score"] * 100),
                "seo": round(cat["seo"]["score"] * 100),
            }
        except Exception as e:
            results[strategy] = {"error": str(e)}

    return results
