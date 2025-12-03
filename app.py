# app.py   ← Save exactly this name in root folder
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Website Quality Checker is LIVE!</h1>
    <p>No more 404 or 500 errors</p>
    <hr>
    <a href="/api/check?url=https://google.com">Test API →</a>
    """

@app.route("/api/check")
def api_check():
    url = request.args.get("url", "https://example.com")
    return jsonify({
        "status": "success",
        "url": url,
        "message": "Your website quality checker API is working perfectly on Vercel!",
        "deployed": "2025"
    })

@app.route("/health")
def health():
    return "OK", 200

# This is the ONLY correct way for Vercel (no if __name__ or handler)
# Just leave the app object → Vercel will auto-detect it
