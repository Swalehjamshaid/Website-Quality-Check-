# app.py
from flask import Flask, request, jsonify, make_response
import requests
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup
from io import BytesIO
from weasyprint import HTML
import os  # For env checks

app = Flask(__name__)

# Your existing HTML_TEMPLATE (unchanged)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Quality Checker</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin:0; padding:0; height:100vh; color:#333;}
        .container { max-width: 900px; margin: 40px auto; background:white; border-radius:15px; box-shadow:0 20px 40px rgba(0,0,0,0.2); overflow:hidden;}
        header { background:#4a00e0; color:white; padding:30px; text-align:center;}
        h1 { margin:0; font-size:2.5em;}
        .input-section { padding:40px; text-align:center; background:#f8f9fa;}
        input[type=text] { width:70%; padding:15px; font-size:18px; border:2px solid #ddd; border-radius:8px;}
        button { padding:15px 30px; font-size:18px; background:#4a00e0; color:white; border:none; border-radius:8px; cursor:pointer; margin-left:10px;}
        button:hover { background:#3a00b0;}
        .result { padding:30px; display:none;}
        table { width:100%; border-collapse:collapse; margin-top:20px;}
        th, td { padding:12px; text-align:left; border-bottom:1px solid #ddd;}
        th { background:#f0f0f0;}
        .good { color:green; font-weight:bold;}
        .bad { color:red; font-weight:bold;}
        footer { text-align:center; padding:20px; background:#333; color:white;}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Website Quality Checker</h1>
            <p>Instant SEO, Speed & Security Audit</p>
        </header>
       
        <div class="input-section">
            <form onsubmit="check(event)">
                <input type="text" id="url" placeholder="Enter website URL (e.g. https://google.com)" required>
                <button type="submit">Check Now</button>
            </form>
        </div>
       
        <div class="result" id="result"></div>
    </div>
    <script>
        function check(e) {
            e.preventDefault();
            const url = document.getElementById('url').value;
            if (!url.startsWith('http')) return alert('Please include https://');
            document.getElementById('result').style.display = 'block';
            document.getElementById('result').innerHTML = '<p>Checking...</p>';
           
            fetch(`/api/check?url=${encodeURIComponent(url)}`)
                .then(r => r.json())
                .then(data => {
                    document.getElementById('result').innerHTML = data.html;
                });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return HTML_TEMPLATE

# Get grade from score
def get_grade(score):
    if score >= 90: return "A (Excellent)"
    elif score >= 80: return "B (Good)"
    elif score >= 70: return "C (Fair)"
    elif score >= 60: return "D (Poor)"
    else: return "F (Critical Issues)"

# Recommendations dictionary (unchanged)
RECOMMENDATIONS = {
    "SSL/HTTPS": "Install a free SSL certificate from Let's Encrypt or Cloudflare to enable HTTPS.",
    "Load Time": "Optimize images, minify CSS/JS, and use a CDN to reduce load time below 3 seconds.",
    "Page Size": "Compress images and remove unnecessary code to keep page size under 2MB.",
    "Title Length": "Adjust title to 30-60 characters for better SEO.",
    "Meta Description Length": "Add a meta description of 120-160 characters.",
    "Mobile Friendly (Viewport)": "Add <meta name='viewport' content='width=device-width, initial-scale=1'> to your HTML head.",
    "Images with Alt Text": "Add alt attributes to all <img> tags for accessibility and SEO.",
    "Headings Present": "Add at least one <h1> and structured <h2>/<h3> headings.",
    "Broken Links": "Fix or remove broken links using tools like Ahrefs or manual checks.",
    "GZIP Compression": "Enable GZIP compression on your server (e.g., in .htaccess for Apache).",
    "HSTS Header": "Add Strict-Transport-Security header to your server config.",
    "CSP Header": "Implement Content-Security-Policy header to prevent XSS attacks.",
    "X-Frame-Options": "Add X-Frame-Options: DENY to prevent clickjacking.",
    "Basic Accessibility (WCAG)": "Ensure alt texts, headings, and color contrast meet WCAG standards.",
    "SEO Basics Score": "Optimize title, meta desc, and headings for better search rankings."
}

@app.route("/api/check")
def api_check():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
   
    if not url.startswith("http"):
        url = "https://" + url
   
    start_time = time.time()
    try:
        headers = {"User-Agent": "Website-Quality-Checker/1.0"}
        r = requests.get(url, timeout=15, allow_redirects=True, headers=headers)
        load_time = round(time.time() - start_time, 2)
        size_kb = len(r.content) // 1024
       
        parsed = urlparse(r.url)
        is_https = parsed.scheme == "https"
        final_url = r.url
       
        soup = BeautifulSoup(r.text, 'html.parser')
       
        title = soup.title.string if soup.title else "No Title"
        title_length = len(title) if title else 0
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_desc_length = len(meta_desc["content"]) if meta_desc else 0
        has_viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
        has_alt_images = all(img.get("alt") for img in soup.find_all("img")) if soup.find_all("img") else True
        heading_count = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        has_h1 = bool(soup.find("h1"))
        # Limit broken links check to avoid timeout (check only first 5)
        broken_links = []
        links = soup.find_all("a", href=True)[:5]
        for a in links:
            if a['href'].startswith("http"):
                try:
                    if requests.head(a['href'], timeout=3).status_code >= 400:
                        broken_links.append(a['href'])
                except:
                    pass
        num_broken_links = len(broken_links)
        has_gzip = r.headers.get("Content-Encoding", "").lower() == "gzip"
        security_headers = {
            "HSTS": "Strict-Transport-Security" in r.headers,
            "CSP": "Content-Security-Policy" in r.headers,
            "X-Frame-Options": "X-Frame-Options" in r.headers
        }
        accessibility_basics = has_alt_images and has_h1 and heading_count > 0
        mobile_friendly = has_viewport
        seo_score = (1 if 30 < title_length < 60 else 0) + (1 if 120 < meta_desc_length < 160 else 0) + (1 if has_h1 else 0)
       
        score = 100
        if not is_https: score -= 20
        if load_time > 3: score -= 15
        if size_kb > 2000: score -= 10
        if num_broken_links > 0: score -= 10
        if not has_gzip: score -= 5
        if not all(security_headers.values()): score -= 15
        if not accessibility_basics: score -= 15
        if not mobile_friendly: score -= 10

        grade = get_grade(score)
       
        # Build rows with real data (no placeholders)
        rows = [
            {"metric": "Final URL", "value": final_url, "status": "OK", "rec": ""},
            {"metric": "HTTP Status", "value": r.status_code, "status": "Good" if r.status_code == 200 else "Check", "rec": "" if r.status_code == 200 else "Investigate server errors."},
            {"metric": "Load Time", "value": f"{load_time} sec", "status": "Fast" if load_time < 3 else "Slow", "rec": RECOMMENDATIONS["Load Time"] if load_time >= 3 else ""},
            {"metric": "Page Size", "value": f"{size_kb} KB", "status": "Light" if size_kb < 2000 else "Heavy", "rec": RECOMMENDATIONS["Page Size"] if size_kb >= 2000 else ""},
            {"metric": "SSL/HTTPS", "value": "Yes" if is_https else "No", "status": "Secure" if is_https else "Not Secure", "rec": RECOMMENDATIONS["SSL/HTTPS"] if not is_https else ""},
            {"metric": "Title Length", "value": f"{title_length} chars", "status": "Optimal" if 30 < title_length < 60 else "Adjust", "rec": RECOMMENDATIONS["Title Length"] if not (30 < title_length < 60) else ""},
            {"metric": "Meta Description Length", "value": f"{meta_desc_length} chars", "status": "Optimal" if 120 < meta_desc_length < 160 else "Adjust", "rec": RECOMMENDATIONS["Meta Description Length"] if not (120 < meta_desc_length < 160) else ""},
            {"metric": "Mobile Friendly (Viewport)", "value": "Yes" if has_viewport else "No", "status": "Good" if has_viewport else "Improve", "rec": RECOMMENDATIONS["Mobile Friendly (Viewport)"] if not has_viewport else ""},
            {"metric": "Images with Alt Text", "value": "Yes" if has_alt_images else "No", "status": "Compliant" if has_alt_images else "Missing", "rec": RECOMMENDATIONS["Images with Alt Text"] if not has_alt_images else ""},
            {"metric": "Headings Present", "value": heading_count, "status": "Good" if heading_count > 0 else "Add", "rec": RECOMMENDATIONS["Headings Present"] if heading_count == 0 else ""},
            {"metric": "Broken Links", "value": num_broken_links, "status": "None" if num_broken_links == 0 else "Fix", "rec": RECOMMENDATIONS["Broken Links"] if num_broken_links > 0 else ""},
            {"metric": "GZIP Compression", "value": "Yes" if has_gzip else "No", "status": "Enabled" if has_gzip else "Enable", "rec": RECOMMENDATIONS["GZIP Compression"] if not has_gzip else ""},
            {"metric": "HSTS Header", "value": "Yes" if security_headers['HSTS'] else "No", "status": "Secure" if security_headers['HSTS'] else "Add", "rec": RECOMMENDATIONS["HSTS Header"] if not security_headers['HSTS'] else ""},
            {"metric": "CSP Header", "value": "Yes" if security_headers['CSP'] else "No", "status": "Secure" if security_headers['CSP'] else "Add", "rec": RECOMMENDATIONS["CSP Header"] if not security_headers['CSP'] else ""},
            {"metric": "X-Frame-Options", "value": "Yes" if security_headers['X-Frame-Options'] else "No", "status": "Secure" if security_headers['X-Frame-Options'] else "Add", "rec": RECOMMENDATIONS["X-Frame-Options"] if not security_headers['X-Frame-Options'] else ""},
            {"metric": "Basic Accessibility (WCAG)", "value": "Compliant" if accessibility_basics else "Needs Work", "status": "Good" if accessibility_basics else "Improve", "rec": RECOMMENDATIONS["Basic Accessibility (WCAG)"] if not accessibility_basics else ""},
            {"metric": "SEO Basics Score", "value": f"{seo_score}/3", "status": "Excellent" if seo_score == 3 else "Optimize", "rec": RECOMMENDATIONS["SEO Basics Score"] if seo_score < 3 else ""},
            {"metric": "Overall Quality Score", "value": f"<strong>{score}/100</strong>", "status": "Excellent" if score >= 80 else "Needs Improvement", "rec": ""},
        ]

        # Build HTML table
        table_html = "<table><tr><th>Metric</th><th>Value</th><th>Status</th><th>Recommendation</th></tr>"
        for row in rows:
            status_class = "good" if any(good in row["status"].lower() for good in ["good", "excellent", "secure", "fast", "light", "optimal", "compliant", "enabled", "none", "ok"]) else "bad"
            table_html += f"<tr><td>{row['metric']}</td><td>{row['value']}</td><td class='{status_class}'>{row['status']}</td><td>{row['rec']}</td></tr>"
        table_html += "</table>"

        html = f"""
        <h2>Results for <code>{final_url}</code></h2>
        <p>Overall Grade: <strong>{grade}</strong></p>
        {table_html}
        <p><a href="/">← Check Another Website</a> | <a href="/api/pdf?url={url}">Download PDF Report</a> | <a href="/api/pdf?url={url}&white_label=true">White-Label PDF</a></p>
        """
        return jsonify({"html": html, "data": {
            "url": url,
            "final_url": final_url,
            "score": score,
            "grade": grade,
            "rows": rows,
            "table_html": table_html  # Pass full table for PDF
        }})
   
    except Exception as e:
        return jsonify({"html": f"<p class='bad'>Error: {str(e)}</p><a href='/'>← Back</a>"})

@app.route("/api/pdf")
def generate_pdf():
    url = request.args.get("url")
    white_label = request.args.get("white_label", "false").lower() == "true"
    if not url:
        return "No URL provided", 400

    try:
        # Call api_check to get real data
        check_result = api_check()
        if check_result.status_code != 200:
            return "Error fetching audit data", 500
        data = check_result.get_json()["data"]

        # Use passed table_html (real data)
        table_html = data["table_html"]

        # Build full PDF HTML (professional format)
        branding = "" if white_label else "<p style='text-align: center; font-size: 12px; color: #666;'>Powered by Website Quality Checker</p>"
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; page-break-before: avoid; }}
                h1 {{ color: #4a00e0; text-align: center; page-break-after: avoid; }}
                h2 {{ color: #333; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; page-break-inside: avoid; }}
                th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
                th {{ background: #f0f0f0; font-weight: bold; }}
                .good {{ color: green; font-weight: bold; }}
                .bad {{ color: red; font-weight: bold; }}
                .header {{ background: #4a00e0; color: white; padding: 30px; text-align: center; margin-bottom: 20px; page-break-after: avoid; }}
                .summary {{ margin: 20px 0; font-size: 1.2em; text-align: center; background: #f8f9fa; padding: 20px; border-radius: 8px; }}
                .grade {{ font-size: 3em; color: #4a00e0; }}
                @page {{ size: A4; margin: 20mm; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Website Quality Audit Report</h1>
                <h2>{data['url']}</h2>
                <p>Generated on {time.strftime('%B %d, %Y %H:%M')}</p>
            </div>
            <div class="summary">
                <p><strong>Overall Score: {data['score']}/100</strong></p>
                <p class="grade">{data['grade']}</p>
                <p>Your site scores {data['score']}/100. Focus on recommendations for quick wins.</p>
            </div>
            <h2>Detailed Metrics & Recommendations</h2>
            {table_html}
            <div style="margin-top: 40px; page-break-before: avoid;">
                <h3>Next Steps</h3>
                <p>Prioritize fixes marked in red. Retest after changes for improved score.</p>
                {branding}
            </div>
        </body>
        </html>
        """

        # Generate PDF with error handling
        pdf = HTML(string=full_html).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        filename = f"audit-report-{url.split('//')[-1].split('/')[0]}.pdf"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    except ImportError as e:
        # Fallback if WeasyPrint fails
        return jsonify({"error": f"WeasyPrint not available: {str(e)}. Use basic report."}), 500
    except Exception as e:
        return f"PDF generation error: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
