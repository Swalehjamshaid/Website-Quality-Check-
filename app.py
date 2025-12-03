# app.py  ← Replace your entire file with this
from flask import Flask, request, jsonify
import requests
from urllib.parse import urlparse
import time

app = Flask(__name__)

# Beautiful HTML + CSS (single file – no extra folders needed)
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

@app.route("/api/check")
def api_check():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    if not url.startswith("http"):
        url = "https://" + url
    
    start_time = time.time()
    try:
        r = requests.get(url, timeout=15, allow_redirects=True, headers={"User-Agent": "Website-Quality-Checker"})
        load_time = round(time.time() - start_time, 2)
        size_kb = len(r.content) // 1024
        
        parsed = urlparse(r.url)
        is_https = parsed.scheme == "https"
        final_url = r.url
        
        score = 100
        if not is_https: score -= 30
        if load_time > 3: score -= 20
        if size_kb > 3000: score -= 15
        
        html = f"""
        <h2>Results for <code>{final_url}</code></h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Status</th></tr>
            <tr><td>Final URL</td><td>{final_url}</td><td>OK</td></tr>
            <tr><td>HTTP Status</td><td>{r.status_code}</td><td class="{'good' if r.status_code==200 else 'bad'}">{'Good' if r.status_code==200 else 'Check'}</td></tr>
            <tr><td>Load Time</td><td>{load_time} sec</td><td class="{'good' if load_time<3 else 'bad'}">{'Fast' if load_time<3 else 'Slow'}</td></tr>
            <tr><td>Page Size</td><td>{size_kb} KB</td><td class="{'good' if size_kb<2000 else 'bad'}">{'Light' if size_kb<2000 else 'Heavy'}</td></tr>
            <tr><td>SSL/HTTPS</td><td>{'Yes' if is_https else 'No'}</td><td class="{'good' if is_https else 'bad'}">{'Secure' if is_https else 'Not Secure'}</td></tr>
            <tr><td>Quality Score</td><td><strong>{score}/100</strong></td><td class="{'good' if score>=80 else 'bad'}">{'Excellent' if score>=80 else 'Needs Improvement'}</td></tr>
        </table>
        <p><a href="/">← Check Another Website</a></p>
        """
        return jsonify({"html": html})
    
    except Exception as e:
        return jsonify({"html": f"<p class='bad'>Error: {str(e)}</p><a href='/'>← Back</a>"})

if __name__ == "__main__":
    app.run()
