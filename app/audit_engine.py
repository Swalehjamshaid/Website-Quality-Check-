"""
app/audit_engine.py
Provides run_all_metrics(url, pagespeed_api_key=None) which returns a JSON-serializable dict
containing 37 metrics and helpful fields.

Note: for exact Lighthouse vitals you must set PAGESPEED_API_KEY in env.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time
import socket
import ssl

HEADERS = {"User-Agent": "37Metrics-Pro-Auditor/1.0 (+https://37metrics.live)"}
DEFAULT_TIMEOUT = 20

def fetch(url, timeout=DEFAULT_TIMEOUT):
    resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp

def domain_of(url):
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"

def get_soup(text):
    return BeautifulSoup(text, "html.parser")

# -- Metric implementations (1..37) --
# 1) PageSpeed / Lighthouse (requires API key)
def metric_pagespeed(final_url, api_key=None, strategy="mobile"):
    if not api_key:
        return {"available": False}
    api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {"url": final_url, "strategy": strategy, "key": api_key,
              "category": ["performance", "accessibility", "best-practices", "seo", "pwa"]}
    r = requests.get(api, params=params, timeout=60)
    if r.status_code != 200:
        return {"available": False, "status_code": r.status_code}
    payload = r.json()
    lr = payload.get("lighthouseResult", {})
    cats = lr.get("categories", {})
    audits = lr.get("audits", {})
    return {
        "available": True,
        "performance": round(cats.get("performance", {}).get("score", 0) * 100, 1),
        "accessibility": round(cats.get("accessibility", {}).get("score", 0) * 100, 1),
        "best_practices": round(cats.get("best-practices", {}).get("score", 0) * 100, 1),
        "seo": round(cats.get("seo", {}).get("score", 0) * 100, 1),
        "pwa": round(cats.get("pwa", {}).get("score", 0) * 100, 1),
        "lcp": audits.get("largest-contentful-paint", {}).get("displayValue"),
        "cls": audits.get("cumulative-layout-shift", {}).get("displayValue"),
        "fcp": audits.get("first-contentful-paint", {}).get("displayValue"),
        "tti": audits.get("interactive", {}).get("displayValue"),
        "raw": payload
    }

# 2) page_size_kb
def metric_page_size(resp):
    return {"page_size_kb": round(len(resp.content) / 1024, 1)}

# 3) total_requests estimate
def metric_total_requests(soup, base):
    tags = soup.find_all(["script", "img", "link", "iframe", "video", "audio", "source"])
    urls = set()
    for t in tags:
        if t.name == "script" and t.get("src"):
            urls.add(urljoin(base, t["src"]))
        if t.name == "img" and t.get("src"):
            urls.add(urljoin(base, t["src"]))
        if t.name == "link" and t.get("href"):
            urls.add(urljoin(base, t["href"]))
        if t.name in ("iframe", "video", "audio", "source") and t.get("src"):
            urls.add(urljoin(base, t["src"]))
    return {"total_requests_est": len(urls)}

# 4) has_https
def metric_has_https(final_url):
    return {"has_https": final_url.startswith("https://")}

# 5) server_response_time
def metric_server_response_time(resp):
    try:
        return {"server_response_time_s": resp.elapsed.total_seconds()}
    except Exception:
        return {"server_response_time_s": None}

# 6) title_tag
def metric_title_tag(soup):
    ok = bool(soup.title and soup.title.string and soup.title.string.strip())
    return {"title_tag": ok, "title_text": (soup.title.string.strip() if soup.title else "")}

# 7) meta_description
def metric_meta_description(soup):
    tag = soup.find("meta", attrs={"name": "description"})
    return {"meta_description": bool(tag), "meta_description_content": tag["content"].strip() if tag and tag.get("content") else ""}

# 8) viewport_tag
def metric_viewport_tag(soup):
    tag = soup.find("meta", attrs={"name": "viewport"})
    return {"viewport_tag": bool(tag)}

# 9) robots_txt
def metric_robots_txt(final_url):
    try:
        root = domain_of(final_url)
        r = requests.head(root + "/robots.txt", timeout=8, headers=HEADERS, allow_redirects=True)
        return {"robots_txt": r.status_code == 200}
    except Exception:
        return {"robots_txt": False}

# 10) sitemap_xml
def metric_sitemap_xml(final_url):
    try:
        root = domain_of(final_url)
        r = requests.head(root + "/sitemap.xml", timeout=8, headers=HEADERS, allow_redirects=True)
        return {"sitemap_xml": r.status_code == 200}
    except Exception:
        return {"sitemap_xml": False}

# 11) canonical_tag
def metric_canonical_tag(soup):
    tag = soup.find("link", rel="canonical")
    return {"canonical_tag": bool(tag), "canonical_href": tag["href"] if tag and tag.get("href") else ""}

# 12) hreflang_tags
def metric_hreflang_tags(soup):
    tags = soup.find_all("link", attrs={"rel": "alternate"})
    hreflangs = [t.get("hreflang") for t in tags if t.get("hreflang")]
    return {"hreflang_tags": len(hreflangs) > 0, "hreflang_values": hreflangs}

# 13) mobile_friendly estimate
def metric_mobile_friendly(soup):
    viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
    mobile_class = bool(soup.find(attrs={"class": re.compile(r"(mobile|responsive|viewport)")}))
    return {"mobile_friendly_est": viewport or mobile_class}

# 14) structured_data
def metric_structured_data(soup):
    jlds = soup.find_all("script", attrs={"type": "application/ld+json"})
    return {"structured_data": len(jlds) > 0, "ld_count": len(jlds)}

# 15) open_graph_tags
def metric_open_graph_tags(soup):
    tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:")})
    return {"open_graph_tags": len(tags) > 0, "og_count": len(tags)}

# 16) twitter_cards
def metric_twitter_cards(soup):
    tags = soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")})
    return {"twitter_cards": len(tags) > 0, "twitter_count": len(tags)}

# 17) favicon
def metric_favicon(soup, final_url):
    tag = soup.find("link", rel=re.compile(r"icon", re.I))
    if tag and tag.get("href"):
        return {"favicon": True, "favicon_url": urljoin(final_url, tag["href"])}
    try:
        root = domain_of(final_url)
        r = requests.head(root + "/favicon.ico", timeout=6, headers=HEADERS)
        return {"favicon": r.status_code == 200, "favicon_url": (root + "/favicon.ico") if r.status_code == 200 else ""}
    except Exception:
        return {"favicon": False}

# 18) gzip_compression
def metric_gzip_compression(resp):
    enc = resp.headers.get("content-encoding", "")
    return {"gzip_compression": ("gzip" in enc.lower() or "br" in enc.lower())}

# 19) cache_headers
def metric_cache_headers(resp):
    cc = resp.headers.get("cache-control", "")
    expires = resp.headers.get("expires", "")
    return {"cache_control": bool(cc), "cache_control_value": cc, "expires": bool(expires), "expires_value": expires}

# 20) image_optimized (heuristic)
def metric_image_optimized(soup, final_url):
    imgs = soup.find_all("img")
    large = 0
    modern = 0
    checked = 0
    for img in imgs[:50]:
        src = img.get("src")
        if not src:
            continue
        src_url = urljoin(final_url, src)
        try:
            r = requests.head(src_url, timeout=6, headers=HEADERS, allow_redirects=True)
            ct = r.headers.get("content-type", "")
            if "webp" in ct or "avif" in ct:
                modern += 1
            size = int(r.headers.get("content-length") or 0)
            if size > 100_000:
                large += 1
            checked += 1
        except Exception:
            continue
    return {"image_checked": checked, "modern_image_count": modern, "large_images_count": large}

# 21) js_minified (heuristic)
def metric_js_minified(soup, final_url):
    scripts = [urljoin(final_url, s["src"]) for s in soup.find_all("script") if s.get("src")]
    minified = 0
    checked = 0
    for src in scripts[:20]:
        try:
            r = requests.get(src, timeout=8, headers=HEADERS)
            text = r.text.replace("\n", "")
            checked += 1
            if len(text) / (r.text.count("\n") + 1) > 200:
                minified += 1
        except Exception:
            continue
    return {"js_files_checked": checked, "js_minified_count_est": minified}

# 22) css_minified (heuristic)
def metric_css_minified(soup, final_url):
    links = [urljoin(final_url, l["href"]) for l in soup.find_all("link", rel="stylesheet") if l.get("href")]
    minified = 0
    checked = 0
    for href in links[:20]:
        try:
            r = requests.get(href, timeout=8, headers=HEADERS)
            text = r.text.replace("\n", "")
            checked += 1
            if len(text) / (r.text.count("\n") + 1) > 200:
                minified += 1
        except Exception:
            continue
    return {"css_files_checked": checked, "css_minified_count_est": minified}

# 23) unused_css heuristic
def metric_unused_css(soup, final_url):
    links = [urljoin(final_url, l["href"]) for l in soup.find_all("link", rel="stylesheet") if l.get("href")]
    big_css = 0
    for href in links[:20]:
        try:
            r = requests.head(href, timeout=8, headers=HEADERS, allow_redirects=True)
            size = int(r.headers.get("content-length") or 0)
            if size > 150_000:
                big_css += 1
        except Exception:
            continue
    return {"maybe_unused_css_files": big_css, "stylesheets_checked": len(links[:20])}

# 24) unused_js heuristic
def metric_unused_js(soup, final_url):
    scripts = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    third_party = [s for s in scripts if s and urlparse(urljoin(final_url, s)).netloc != urlparse(final_url).netloc]
    return {"third_party_js_count_est": len(third_party), "scripts_count": len(scripts)}

# 25) render_blocking_resources
def metric_render_blocking(soup):
    head = soup.head
    blocking = 0
    if not head:
        return {"render_blocking_resources_est": 0}
    for script in head.find_all("script"):
        if not script.get("async") and not script.get("defer") and script.get("src"):
            blocking += 1
    for link in head.find_all("link", rel="stylesheet"):
        blocking += 1
    return {"render_blocking_resources_est": blocking}

# 26) third_party_js domains
def metric_third_party_js(soup, final_url):
    scripts = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    domains = {}
    for s in scripts:
        if not s:
            continue
        full = urljoin(final_url, s)
        host = urlparse(full).netloc
        if host and host != urlparse(final_url).netloc:
            domains[host] = domains.get(host, 0) + 1
    sorted_top = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]
    return {"third_party_js_domains": sorted_top}

# 27) font_display_swap
def metric_font_display_swap(soup, final_url):
    links = [urljoin(final_url, l["href"]) for l in soup.find_all("link", rel="stylesheet") if l.get("href")]
    found_swap = False
    for href in links[:10]:
        try:
            r = requests.get(href, timeout=8, headers=HEADERS)
            if "font-display" in r.text:
                found_swap = True
                break
        except Exception:
            continue
    return {"font_display_swap": found_swap}

# 28) preload_key_requests
def metric_preload_key_requests(soup):
    preloads = soup.find_all("link", rel=re.compile(r"preload", re.I))
    return {"preload_key_requests": len(preloads)}

# 29) modern_image_formats
def metric_modern_image_formats(soup, final_url):
    imgs = soup.find_all("img")
    modern = 0
    total = 0
    for img in imgs[:50]:
        src = img.get("src")
        if not src:
            continue
        total += 1
        if src.lower().endswith((".webp", ".avif")):
            modern += 1
    return {"modern_image_formats_count": modern, "images_sampled": total}

# 30) lazy_loading
def metric_lazy_loading(soup):
    images = soup.find_all("img")
    lazy = sum(1 for i in images if i.get("loading") == "lazy")
    return {"lazy_loading_count": lazy, "imgs_total": len(images)}

# 31) no_vulnerable_js detection (heuristic)
def metric_no_vulnerable_js(soup):
    scripts = [s.get("src") or "" for s in soup.find_all("script")]
    vuln_signs = []
    for s in scripts:
        if "jquery" in s.lower():
            m = re.search(r"jquery[-\.]?(\d+\.\d+\.\d+)", s)
            if m:
                v = m.group(1)
                try:
                    parts = [int(x) for x in v.split(".")]
                    if parts[0] < 3 or (parts[0] == 3 and parts[1] < 5):
                        vuln_signs.append({"lib": "jquery", "version": v, "src": s})
                except Exception:
                    vuln_signs.append({"lib": "jquery", "version": v, "src": s})
    return {"vulnerable_js_signatures": vuln_signs, "vulnerable_count": len(vuln_signs)}

# 32) no_mixed_content
def metric_no_mixed_content(soup, final_url):
    parsed = urlparse(final_url)
    if parsed.scheme != "https":
        return {"no_mixed_content": True, "note": "origin not https"}
    resources = []
    for tag in soup.find_all(src=True):
        src = urljoin(final_url, tag["src"])
        if src.startswith("http://"):
            resources.append(src)
    return {"no_mixed_content": len(resources) == 0, "mixed_resources_count": len(resources), "samples": resources[:10]}

# 33) valid_ssl
def metric_valid_ssl(final_url):
    parsed = urlparse(final_url)
    host = parsed.netloc.split(":")[0]
    if not final_url.startswith("https://"):
        return {"valid_ssl": False, "note": "not https"}
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=6) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                return {"valid_ssl": True, "issuer": cert.get("issuer")}
    except Exception as e:
        return {"valid_ssl": False, "error": str(e)}

# 34) grade
def metric_grade(scores):
    vals = [scores.get(k) for k in ("performance", "accessibility", "best_practices", "seo")]
    num = [v for v in vals if isinstance(v, (int, float))]
    if not num:
        return {"grade": "F", "overall_score": 0}
    avg = sum(num) / len(num)
    grade = "A" if avg >= 90 else "B" if avg >= 80 else "C" if avg >= 70 else "D" if avg >= 60 else "F"
    return {"grade": grade, "overall_score": round(avg, 1)}

# 35) robots directives
def metric_robots_directives(final_url):
    try:
        root = domain_of(final_url)
        r = requests.get(root + "/robots.txt", timeout=8, headers=HEADERS)
        text = r.text if r.status_code == 200 else ""
        sitemap = bool(re.search(r"^Sitemap:", text, flags=re.I | re.M))
        crawl_delay = bool(re.search(r"Crawl-delay:", text, flags=re.I | re.M))
        return {"robots_present": r.status_code == 200, "sitemap_directive": sitemap, "crawl_delay_directive": crawl_delay}
    except Exception:
        return {"robots_present": False}

# 36) server technology
def metric_server_technology(resp, soup):
    server = resp.headers.get("server")
    generator = ""
    gen_tag = soup.find("meta", attrs={"name": "generator"})
    if gen_tag and gen_tag.get("content"):
        generator = gen_tag["content"]
    return {"server_header": server, "meta_generator": generator}

# 37) content-security-policy
def metric_csp(resp):
    csp = resp.headers.get("content-security-policy")
    return {"content_security_policy": bool(csp), "csp_header": csp or ""}

# Runner - calls all metrics and composes final dict
def run_all_metrics(url, pagespeed_api_key=None, strategy="mobile"):
    out = {}
    start_ts = int(time.time())
    try:
        resp = fetch(url)
        final_url = resp.url
        soup = get_soup(resp.text)
    except Exception as e:
        return {"error": f"Failed to fetch page: {str(e)}", "timestamp": start_ts}

    # 1) pagespeed (optional)
    pagespeed_res = metric_pagespeed(final_url, api_key=pagespeed_api_key, strategy=strategy) if pagespeed_api_key else {"available": False}
    out["pagespeed"] = pagespeed_res

    # Basic metrics
    out.update(metric_page_size(resp))
    out.update(metric_total_requests(soup, final_url))
    out.update(metric_has_https(final_url))
    out.update(metric_server_response_time(resp))

    # Meta / SEO / headers
    out.update(metric_title_tag(soup))
    out.update(metric_meta_description(soup))
    out.update(metric_viewport_tag(soup))
    out.update(metric_robots_txt(final_url))
    out.update(metric_sitemap_xml(final_url))
    out.update(metric_canonical_tag(soup))
    out.update(metric_hreflang_tags(soup))
    out.update(metric_mobile_friendly(soup))
    out.update(metric_structured_data(soup))
    out.update(metric_open_graph_tags(soup))
    out.update(metric_twitter_cards(soup))
    out.update(metric_favicon(soup, final_url))
    out.update(metric_gzip_compression(resp))

    # Performance heuristics
    out.update(metric_cache_headers(resp))
    out.update(metric_image_optimized(soup, final_url))
    out.update(metric_js_minified(soup, final_url))
    out.update(metric_css_minified(soup, final_url))
    out.update(metric_unused_css(soup, final_url))
    out.update(metric_unused_js(soup, final_url))
    out.update(metric_render_blocking(soup))
    out.update(metric_third_party_js(soup, final_url))
    out.update(metric_font_display_swap(soup, final_url))
    out.update(metric_preload_key_requests(soup))
    out.update(metric_modern_image_formats(soup, final_url))
    out.update(metric_lazy_loading(soup))

    # Security / server
    out.update(metric_no_vulnerable_js(soup))
    out.update(metric_no_mixed_content(soup, final_url))
    out.update(metric_valid_ssl(final_url))

    # Scores & grade
    scores = {
        "performance": pagespeed_res.get("performance") if pagespeed_res.get("available") else 0,
        "accessibility": pagespeed_res.get("accessibility") if pagespeed_res.get("available") else 0,
        "best_practices": pagespeed_res.get("best_practices") if pagespeed_res.get("available") else 0,
        "seo": pagespeed_res.get("seo") if pagespeed_res.get("available") else 0
    }
    out.update(metric_grade(scores))
    out.update(metric_robots_directives(final_url))
    out.update(metric_server_technology(resp, soup))
    out.update(metric_csp(resp))

    out["fetched_url"] = final_url
    out["timestamp"] = start_ts
    return out
