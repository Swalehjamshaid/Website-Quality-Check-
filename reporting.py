# reporting.py
from weasyprint import HTML
import json
import io
from datetime import datetime

def generate_pdf_report(result_data):
    """
    Generates a PDF report using WeasyPrint.
    :param result_data: A dictionary containing the audit result, including website(url).
    :return: A BytesIO stream containing the PDF, or None on failure.
    """
    try:
        data = json.loads(result_data['raw_data'])
        
        website_url = result_data['websites']['url'] if result_data.get('websites') else "N/A"
        lh_scores = data.get('lighthouse_scores', {})
        crawler_data = data.get('crawler_data', {})
        
        # --- HTML Content Generation ---
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Audit Report - {website_url}</title>
            <style>
                body {{ font-family: sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #1e88e5; border-bottom: 3px solid #ccc; padding-bottom: 10px; }}
                .score-box {{ background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                .score-detail {{ font-size: 1.1em; margin-bottom: 8px; font-weight: bold; }}
                .score-high {{ color: #4CAF50; }}
                .score-low {{ color: #F44336; }}
            </style>
        </head>
        <body>
            <h1>Website Quality Audit Report</h1>
            <p><strong>Website URL:</strong> {website_url}</p>
            <p><strong>Audit Date:</strong> {result_data['timestamp'][:19].replace('T', ' ')}</p>
            
            <h2>Overall Score: {data.get('final_score', 0):.0f}%</h2>
            
            <h3>Lighthouse Breakdown</h3>
            <div class="score-box">
                <div class="score-detail score-{'high' if lh_scores.get('performance_score', 0) > 70 else 'low'}">
                    Performance: {lh_scores.get('performance_score', 'N/A')}%
                </div>
                <div class="score-detail score-{'high' if lh_scores.get('seo_score', 0) > 70 else 'low'}">
                    SEO: {lh_scores.get('seo_score', 'N/A')}%
                </div>
                <div class="score-detail score-{'high' if lh_scores.get('accessibility_score', 0) > 70 else 'low'}">
                    Accessibility: {lh_scores.get('accessibility_score', 'N/A')}%
                </div>
            </div>
            
            <h3>Technical & Crawler Issues</h3>
            <p><strong>Broken Links Found:</strong> {crawler_data.get('broken_links_count', 'N/A')}</p>
            <p><strong>HTTP Status Code:</strong> {crawler_data.get('status_code', 'N/A')}</p>
            <p><strong>H1 Tag Content:</strong> {crawler_data.get('h1_tag', 'N/A')}</p>

        </body>
        </html>
        """
        
        pdf_bytes = HTML(string=html_content).write_pdf()
        return io.BytesIO(pdf_bytes)

    except Exception as e:
        print(f"Error during PDF generation: {e}")
        return None
