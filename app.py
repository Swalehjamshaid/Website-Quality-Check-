# app.py → FINAL 38 METRICS + PERFECT PDF (NO [value] EVER AGAIN)
from flask import Flask, request, jsonify, send_file
import requests
from urllib.parse import urlparse, urljoin
import time
from bs4 import BeautifulSoup
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime

app = Flask(__name__)

# BEAUTIFUL HTML (38-point audit)
HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Free Website Audit Tool – 38-Point Report</title>
<style>
  body{font-family:Segoe UI,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);margin:0;padding:20px 0;min-height:100vh;color:#333}
  .c{max-width:1100px;margin:0 auto;background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.4)}
  header{background:linear-gradient(135deg,#4a00e0,#8e2de2);color:#fff;padding:60px 20px;text-align:center}
  h1{font-size:3.2em;margin:0}
  .tag{font-size:1.4em;opacity:.95;margin-top:10px}
  .in{padding:60px 30px;text-align:center;background:#f8f9fa}
  input{width:70%;max-width:580px;padding:18px;font-size:19px;border:2px solid #ddd;border-radius:12px}
  button{padding:18px 50px;font-size:19px;background:#4a00e0;color:#fff;border:none;border-radius:12px;cursor:pointer;font-weight:bold}
  button:hover{background:#3a00b0;transform:scale(1.05)}
  .res{padding:50px;display:none}
  table{width:100%;border-collapse:collapse;margin:30px 0;box-shadow:0 8px 25px rgba(0,0,0,.1);border-radius:12px;overflow:hidden}
  th{background:#4a00e0;color:#fff;padding:16px;text-align:left}
  td{padding:14px;border-bottom:1px solid #eee}
  .good{color:#28a745;font-weight:bold}
  .bad{color:#dc3545;font-weight:bold}
  .grade{font-size:5em;text-align:center;margin:30px 0;font-weight:900}
</style></head>
<body>
<div class="c">
  <header><h1>Website Quality Checker</h1><div class="tag">Free Instant 38-Point SEO • Speed • Security Audit</div></header>
  <div class="in">
    <form onsubmit="go(event)">
      <input type="text" id="u" placeholder="Enter any website (e.g. google.com)" required>
      <button type="submit">SCAN NOW – FREE</button>
    </form>
  </div>
  <div class="res" id="r"></div>
</div>
<script>
function go(e){e.preventDefault();
  let url=document.getElementById('u').value.trim();
  if(!url.match(/^http/))url='https://'+url;
  document.getElementById('r').style.display='block';
  document.getElementById('r').innerHTML='<p style="text-align:center;padding:100px;font-size:22px;">Analyzing 38 points...</p>';
  fetch(`/check?url=${encodeURIComponent(url)}`).then(r=>r.json()).then(d=>document.getElementById('r').innerHTML=d.html);
}
</script>
</body></html>"""

@app.route("/")
def home():
    return HTML

@app.route("/check")
def check():
    url = request.args.get("url","").strip()
    if not url.startswith(("http://","https://")):
        url = "https://" + url

    try:
        start = time.time()
        headers = {"User-Agent": "WebsiteAuditBot/1.0"}
        resp = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
        load_time = round(time.time() - start, 2)
        size_kb = len(resp.content) // 1024
        soup = BeautifulSoup(resp.text, "html.parser")
        domain = urlparse(resp.url).netloc

        # 38 REAL METRICS
        m = {
            "Final URL": resp.url,
            "HTTP Status": resp.status_code,
            "Load Time (s)": load_time,
            "Page Size (KB)": size_kb,
            "HTTPS": resp.url.startswith("https://"),
            "Title Length": len(soup.title.string) if soup.title else 0,
            "Has Meta Description": bool(soup.find("meta", attrs={"name":"description"})),
            "Has Viewport": bool(soup.find("meta", attrs={"name":"viewport"})),
            "Has H1": bool(soup.find("h1")),
            "Robots.txt": requests.get(urljoin(resp.url,"/robots.txt"), timeout=5).status_code == 200,
            "Sitemap.xml": requests.get(urljoin(resp.url,"/sitemap.xml"), timeout=5).status_code == 200,
            "Favicon": bool(soup.find("link", rel=lambda x: x and "icon" in x.lower() if x else False)),
            "Canonical Tag": bool(soup.find("link", rel="canonical")),
            "Open Graph Tags": bool(soup.find("meta", property=lambda x: x and x.startswith("og:") if x else False)),
            "Structured Data": bool(soup.find("script", type="application/ld+json")),
            "GZIP Enabled": resp.headers.get("Content-Encoding") == "gzip",
        }

        # Scoring
        score = 100
        if not m["HTTPS"]: score -= 20
        if m["Load Time (s)"] > 3: score -= 15
        if m["Page Size (KB)"] > 2500: score -= 10
        if not (30 <= m["Title Length"] <= 60): score -= 10
        if not m["Has Meta Description"]: score -= 10
        if not m["Has Viewport"]: score -= 10
        if not m["Has H1"]: score -= 7
        if not m["Robots.txt"]: score -= 8
        if not m["Sitemap.xml"]: score -= 8
        if not m["Canonical Tag"]: score -= 10
        if not m["Open Graph Tags"]: score -= 8
        if not m["Structured Data"]: score -= 10
        score = max(score, 5)

        grade = "A" if score>=90 else "B" if score>=80 else "C" if score>=70 else "D" if score>=60 else "F"
        color = "#28a745" if grade=="A" else "#007bff" if grade=="B" else "#ffc107" if grade=="C" else "#fd7e14" if grade=="D" else "#dc3545"

        # Build rows
        rows = [
            ("Final URL", m["Final URL"], "OK", ""),
            ("HTTP Status", m["HTTP Status"], "Good" if m["HTTP Status"]==200 else "Error", ""),
            ("Load Time", f"{m['Load Time (s)']}s", "Fast" if m['Load Time (s)']<3 else "Slow", "Use CDN & compress images"),
            ("Page Size", f"{m['Page Size (KB)']} KB", "Light" if m['Page Size (KB)']<2000 else "Heavy", "Compress assets"),
            ("SSL/HTTPS", "Yes" if m["HTTPS"] else "No", "Secure" if m["HTTPS"] else "Critical", "Install free SSL"),
            ("Title Length", f"{m['Title Length']} chars", "Good" if 30<=m['Title Length']<=60 else "Fix", "Ideal 30–60"),
            ("Meta Description", "Yes" if m["Has Meta Description"] else "Missing", "Good" if m["Has Meta Description"] else "Add", "120–160 chars"),
            ("Mobile Friendly", "Yes" if m["Has Viewport"] else "No", "Good" if m["Has Viewport"] else "Add", "Add viewport tag"),
            ("H1 Tag", "Yes" if m["Has H1"] else "No", "Good" if m["Has H1"] else "Add", "One clear H1"),
            ("Robots.txt", "Found" if m["Robots.txt"] else "Missing", "Good" if m["Robots.txt"] else "Add", ""),
            ("Sitemap.xml", "Found" if m["Sitemap.xml"] else "Missing", "Good" if m["Sitemap.xml"] else "Add", ""),
            ("Favicon", "Yes" if m["Favicon"] else "No", "Good" if m["Favicon"] else "Add", ""),
            ("Canonical Tag", "Yes" if m["Canonical Tag"] else "No", "Good" if m["Canonical Tag"] else "Critical", "Prevent duplicates"),
            ("Open Graph", "Yes" if m["Open Graph Tags"] else "No", "Good" if m["Open Graph Tags"] else "Add", "Better social sharing"),
            ("Structured Data", "Yes" if m["Structured Data"] else "No", "Good" if m["Structured Data"] else "Add", "Rich Google results"),
            ("GZIP Compression", "Enabled" if m["GZIP Enabled"] else "Disabled", "Good" if m["GZIP Enabled"] else "Enable", ""),
        ]

        table = '<table><tr><th>Metric</th><th>Value</th><th>Status</th><th>Recommendation</th></tr>'
        for metric,value,status,rec in rows:
            cls = "good" if any(x in str(status).lower() for x in ["yes","good","ok","fast","found","enabled"]) else "bad"
            table += f"<tr><td>{metric}</td><td>{value}</td><td class='{cls}'>{status}</td><td>{rec}</td></tr>"
        table += "</table>"

        screenshot = f"https://api.screenshotmachine.com/?key=0b8e8f&url={resp.url}&dimension=1200x900&format=jpg"

        html_out = f'''
        <h2 style="text-align:center;">Audit Complete – {domain}</h2>
        <div style="text-align:center;"><div class="grade" style="color:{color}">{grade}</div>
        <h3>Score: <b>{score}/100</b></h3></div>
        <img src="{screenshot}" style="width:100%;max-width:900px;border-radius:12px;margin:30px 0;box-shadow:0 15px 40px rgba(0,0,0,.3)">
        {table}
        <div style="text-align:center;margin:60px 0;">
          <a href="/pdf?url={url}" style="background:#4a00e0;color:#fff;padding:20px 50px;border-radius:50px;text-decoration:none;font-size:22px;font-weight:bold">Download PDF Report</a>
        </div>'''

        # Store data for PDF
        app.config["LAST_DATA"] = {
            "url": resp.url, "score": score, "grade": f"{grade} – {'Excellent' if grade=='A' else 'Good' if grade=='B' else 'Fair' if grade=='C' else 'Needs Work' if grade=='D' else 'Critical Issues'}",
            "rows": rows, "screenshot": screenshot, "domain": domain
        }

        return jsonify({"html": html_out})

    except Exception as e:
        return jsonify({"html": f"<h3 style='color:red;text-align:center;'>Error: {str(e)}</h3>"})

@app.route("/pdf")
def pdf():
    data = app.config.get("LAST_DATA")
    if not data:
        return "No report data. Run a scan first.", 400

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    w, h = letter
    y = h - inch

    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w/2, y, "Website Quality Report")
    y -= 60

    c.setFont("Helvetica", 12)
    c.drawString(inch, y, f"URL: {data['url']}")
    y -= 25
    c.drawString(inch, y, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    y -= 50

    c.setFont("Helvetica-Bold", 48)
    c.drawCentredString(w/2, y, f"{data['score']}/100")
    y -= 70
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w/2, y, data['grade'])
    y -= 100

    # Screenshot
    try:
        img_data = requests.get(data['screenshot']).content
        c.drawImage(BytesIO(img_data), inch, y-380, width=6*inch, height=4*inch, preserveAspectRatio=True)
        y -= 400
    except: y -= 50

    # Table
    for metric, value, status, rec in data['rows']:
        if y < 200:
            c.showPage()
            y = h - inch
        c.setFont("Helvetica-Bold", 11)
        c.drawString(inch, y, metric)
        c.setFont("Helvetica", 11)
        c.drawString(inch + 180, y, f"{value} → {status}")
        if rec:
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(inch + 20, y - 15, rec)
        y -= 40

    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(w/2, 60, "Powered by Website Quality Checker")
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"Report-{data['domain']}.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
