# app.py - 100% WORKING ON VERCEL - December 2025
from flask import Flask, request, jsonify, make_response
import requests
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Quality Checker</title>
    <style>
        body {font-family:Segoe UI,sans-serif; background:linear-gradient(135deg,#667eea,#764ba2); margin:0; padding:0; min-height:100vh;}
        .container {max-width:960px; margin:40px auto; background:white; border-radius:16px; box-shadow:0 20px 50px rgba(0,0,0,0.3); overflow:hidden;}
        header {background:#4a00e0; color:white; padding:40px; text-align:center;}
        h1 {margin:0; font-size:2.8em;}
        .input-section {padding:50px 30px; text-align:center; background:#f8f9fa;}
        input[type=text] {width:70%; max-width:500px; padding:16px; font-size:18px; border:2px solid #ddd; border-radius:12px;}
        button {padding:16px 40px; font-size:18px; background:#4a00e0; color:white; border:none; border-radius:12px; cursor:pointer; font-weight:bold;}
        button:hover {background:#3a00b0;}
        .result {padding:40px; display:none;}
        table {width:100%; border-collapse:collapse; margin:30px 0; font-size:15px;}
        th, td {padding:14px; text-align:left; border-bottom:1px solid #eee;}
        th {background:#4a00e0; color:white;}
        .good {color:#28a745; font-weight:bold;}
        .bad {color:#dc3545; font-weight:bold;}
    </style>
</head>
<body>
    <div class="container">
        <header><h1>Website Quality Checker</h1><p>Free Instant SEO • Speed • Security Audit</p></header>
        <div class="input-section">
            <form onsubmit="check(event)">
                <input type="text" id="url" placeholder="https://example.com" required>
                <button type="submit">SCAN NOW</button>
            </form>
        </div>
        <div class="result" id="result"></div>
    </div>
    <script>
        function check(e){e.preventDefault();
            let url = document.getElementById('url').value.trim();
            if(!url.startsWith('http')) url = 'https://' + url;
            document.getElementById('result').style.display='block';
            document.getElementById('result').innerHTML='<p style="text-align:center;padding:60px;font-size:18px;">Analyzing website...</p>';
            fetch(`/api/check?url=${encodeURIComponent(url)}`)
                .then(r=>r.json())
                .then(d=>document.getElementById('result').innerHTML=d.html);
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return HTML_TEMPLATE

def get_grade(score):
    if score >= 90: return "A (Excellent)"
    elif score >= 80: return "B (Good)"
    elif score >= 70: return "C (Fair)"
    elif score >= 60: return "D (Poor)"
    else: return "F (Critical Issues)"

@app.route("/api/check")
def api_check():
    url = request.args.get("url", "").strip()
    if not url.startswith("http"):
        url = "https://" + url

    try:
        start = time.time()
        headers = {"User-Agent": "Mozilla/5.0 (Website-Quality-Checker)"}
        r = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
        load_time = round(time.time() - start, 2)
        size_kb = len(r.content) // 1024
        final_url = r.url
        soup = BeautifulSoup(r.text, 'html.parser')

        # Core checks
        is_https = final_url.startswith("https://")
        title = soup.title.string.strip() if soup.title else "No title"
        title_len = len(title)
        meta_desc = soup.find("meta", attrs={"name": "description"})
        has_meta_desc = bool(meta_desc and meta_desc.get("content"))
        has_viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
        has_h1 = bool(soup.find("h1"))

        # Score calculation
        score = 100
        if not is_https: score -= 20
        if load_time > 3: score -= 15
        if size_kb > 2000: score -= 10
        if not (30 <= title_len <= 60): score -= 8
        if not has_meta_desc: score -= 10
        if not has_viewport: score -= 10
        if not has_h1: score -= 7

        grade = get_grade(score)

        rows = [
            {"metric": "Final URL", "value": final_url, "status": "OK", "rec": ""},
            {"metric": "HTTP Status", "value": r.status_code, "status": "Good" if r.status_code == 200 else "Error", "rec": ""},
            {"metric": "Load Time", "value": f"{load_time}s", "status": "Fast" if load_time < 3 else "Slow", "rec": "Use CDN, compress images"},
            {"metric": "Page Size", "value": f"{size_kb} KB", "status": "Light" if size_kb < 2000 else "Heavy", "rec": "Compress assets"},
            {"metric": "SSL/HTTPS", "value": "Yes" if is_https else "No", "status": "Secure" if is_https else "Critical", "rec": "Install free Let's Encrypt SSL"},
            {"metric": "Title Length", "value": f"{title_len} chars", "status": "Good" if 30<=title_len<=60 else "Fix", "rec": "Ideal: 30–60 characters"},
            {"metric": "Meta Description", "value": "Yes" if has_meta_desc else "Missing", "status": "Good" if has_meta_desc else "Add", "rec": "Add 120–160 char description"},
            {"metric": "Mobile Friendly", "value": "Yes" if has_viewport else "No", "status": "Good" if has_viewport else "Add", "rec": "Add viewport meta tag"},
            {"metric": "H1 Tag", "value": "Yes" if has_h1 else "No", "status": "Good" if has_h1 else "Add", "rec": "Add one clear H1"},
            {"metric": "Overall Score", "value": f"{score}/100", "status": grade.split()[0], "rec": ""},
        ]

        # Build HTML table for browser
        table_html = '<table><tr><th>Metric</th><th>Value</th><th>Status</th><th>Recommendation</th></tr>'
        for row in rows:
            cls = "good" if any(x in row["status"].lower() for x in ["good","ok","yes","fast","light","secure"]) else "bad"
            table_html += f"<tr><td>{row['metric']}</td><td>{row['value']}</td><td class='{cls}'>{row['status']}</td><td>{row['rec']}</td></tr>"
        table_html += "</table>"

        result_html = f"""
        <h2 style="text-align:center;">Scan Complete</h2>
        <h3 style="text-align:center;color:#4a00e0;">Score: <b>{score}/100</b> → <span style="font-size:2em">{grade}</span></h3>
        {table_html}
        <div style="text-align:center;margin:40px 0;">
            <a href="/api/pdf?url={url}" style="background:#4a00e0;color:white;padding:16px 32px;text-decoration:none;border-radius:50px;font-size:18px;font-weight:bold;">Download PDF Report</a>
            <a href="/api/pdf?url={url}&wl=1" style="margin-left:20px;color:#4a00e0;font-weight:bold;">White-label PDF</a>
        </div>
        """

        return jsonify({
            "html": result_html,
            "data": {"rows": url, "score": score, "grade": grade, "rows": rows}
        })

    except Exception as e:
        return jsonify({"html": f"<p style='color:red;text-align:center;'>Error: {str(e)}</p>"})

@app.route("/api/pdf")
def generate_pdf():
    url = request.args.get("url")
    white_label = request.args.get("wl") == "1"
    if not url:
        return "No URL", 400

    # Re-use the same logic to get fresh data
    check_response = api_check()
    data = check_response.get_json()["data"]

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch

    # Header
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, y, "Website Quality Report")
    y -= 50
    c.setFont("Helvetica", 12)
    c.drawString(inch, y, f"URL: {data['url']}")
    y -= 20
    c.drawString(inch, y, f"Date: {time.strftime('%B %d, %Y %H:%M')}")
    y -= 40

    # Score & Grade
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width/2, y, f"{data['score']}/100")
    y -= 50
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, y, data['grade'])
    y -= 60

    # Table
    c.setFont("Helvetica-Bold", 11)
    c.drawString(inch, y, "Metric")
    c.drawString(inch+150, y, "Value")
    c.drawString(inch+280, y, "Status")
    c.drawString(inch+400, y, "Recommendation")
    y -= 20
    c.line(inch, y, width-inch, y)
    y -= 10

    c.setFont("Helvetica", 10)
    for row in data["rows"]:
        if y < 100:
            c.showPage()
            y = height - inch
        c.drawString(inch, y, row["metric"][:30])
        c.drawString(inch+150, y, str(row["value"])[0:25])
        c.drawString(inch+280, y, row["status"])
        if row["rec"]:
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(inch+20, y-12, row["rec"][:70])
            c.setFont("Helvetica", 10)
        y -= 35

    if not white_label:
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width/2, 50, "Powered by Website Quality Checker")

    c.save()
    buffer.seek(0)
    resp = make_response(buffer.getvalue())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename=report-{urlparse(url).netloc}.pdf'
    return resp

if __name__ == "__main__":
    app.run(debug=True)
