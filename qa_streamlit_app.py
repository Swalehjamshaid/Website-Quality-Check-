import streamlit as st
import random
import time
import io
import pandas as pd
from datetime import datetime
from fpdf import FPDF # Required for PDF generation
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
st.set_page_config(
    page_title="QA Autopilot Dashboard (Streamlit)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PDF GENERATION UTILITY ---

def create_pdf_report(report):
    """Generates a detailed PDF report from the analysis data using fpdf2."""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Title
    pdf.cell(0, 10, "QA Autopilot Website Health Report", 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Website: {report['website_url']}", 0, 1, "C")
    pdf.cell(0, 5, f"Report Date: {datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "C")
    pdf.ln(10)

    # Health Score
    pdf.set_font("Arial", "B", 30)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 20, f"Health Score: {report['health_score']}/100", 0, 1, "C", 1)
    pdf.ln(5)

    # Summary Scores
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Sectional Scores:", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    
    for key, score in report['summary'].items():
        pdf.cell(60, 5, f"{key.capitalize()}: {score}%", 0, 0, "L")
    pdf.ln(8)

    # Issues Found
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Critical Issues Found:", 0, 1, "L")
    if report['issues_found']:
        pdf.set_font("Arial", "", 10)
        for issue in report['issues_found']:
            pdf.cell(0, 5, f"- {issue}", 0, 1, "L")
    else:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 5, "No critical issues detected.", 0, 1, "L")
    pdf.ln(5)
    
    # Detailed Page Crawl Summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Crawl and Testing Summary:", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    
    summary = report.get('pages_tested_summary', {})
    pdf.cell(0, 5, f"Total Pages Crawled: {summary.get('total_pages', 'N/A')}", 0, 1, "L")
    pdf.cell(0, 5, f"Broken Links Found: {summary.get('broken_links', 'N/A')}", 0, 1, "L")
    pdf.cell(0, 5, f"Pages Missing SEO Data: {summary.get('pages_missing_seo', 'N/A')}", 0, 1, "L")
    pdf.cell(0, 5, "Screenshot Status: Mock Screenshot generated successfully.", 0, 1, "L")

    # Output PDF to memory
    pdf_output = pdf.output(dest='S').encode('latin1')
    return io.BytesIO(pdf_output)

# --- EMAIL UTILITY ---

def send_email_report(sender_email, sender_password, recipient_email, report_name, pdf_content):
    """Simulates sending an email with the PDF attachment."""
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"QA Autopilot Report: {report_name}"
    
    body = f"Please find attached the latest Automated QA Health Report for your website, generated on {datetime.now().strftime('%Y-%m-%d')}."
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach PDF
    attachment = MIMEText(pdf_content.getvalue(), 'base64', _subtype="pdf")
    attachment.add_header('Content-Disposition', 'attachment', filename=f"{report_name}.pdf")
    msg.attach(attachment)

    try:
        # Using a common secure SMTP port (587)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return "success"
    except Exception as e:
        return f"Error: {e}"

# --- MOCK TESTING ENGINE ---

def random_score(min_val, max_val):
    """Generates a random score between min_val and max_val (inclusive)."""
    return random.randint(min_val, max_val)

def generate_report_python(url):
    """Simulates the complex backend QA process and generates a report dictionary, now including multi-page checks."""
    
    # Generate scores for each category
    perf_score = random_score(40, 95)
    seo_score = random_score(60, 100)
    security_score = random_score(70, 98)
    mobile_score = random_score(50, 99)
    link_score = random_score(80, 100)

    # Calculate overall health score (weighted average)
    health_score = round((perf_score * 0.25 + seo_score * 0.2 + security_score * 0.2 + mobile_score * 0.15 + link_score * 0.2))

    issues = [
        'Missing H1 tag on homepage',
        'Image sizes are too large (1.5MB+)',
        'Server response time is slow (> 500ms)',
        'CORS policy detected on payment gateway',
        'Broken internal link on the "About Us" page',
        'Viewports are not optimized for tablets',
        'Missing Security Headers (CSP)',
    ]
    
    # --- ENHANCED CRAWL/TESTING SIMULATION ---
    total_pages = random_score(50, 200)
    broken_links = round((100 - link_score) / 100 * total_pages * 0.1)
    pages_missing_seo = round((100 - seo_score) / 100 * total_pages * 0.05)
    
    pages_tested_summary = {
        'total_pages': total_pages,
        'broken_links': broken_links,
        'pages_missing_seo': pages_missing_seo,
        'screenshot_status': 'Mock Screenshot Taken',
    }
    # --- END ENHANCED SIMULATION ---

    detailed_report = {
        'performance': {
            'score': perf_score,
            'metrics': [
                {'name': 'FCP (First Contentful Paint)', 'value': f'{random_score(1, 3)}s', 'status': 'slow' if perf_score < 70 else 'good'},
                {'name': 'Server Response Time', 'value': f'{random_score(100, 800)}ms', 'status': 'slow' if perf_score < 60 else 'ok'},
                {'name': 'Render Blocking Resources', 'value': str(random_score(0, 5)), 'status': 'warn' if perf_score < 80 else 'good'},
            ],
        },
        'seo': {
            'score': seo_score,
            'metrics': [
                {'name': 'Meta Descriptions', 'value': f'{random_score(90, 100)}% coverage', 'status': 'warn' if seo_score < 90 else 'good'},
                {'name': 'Canonical Tags', 'value': f'{random_score(95, 100)}% present', 'status': 'ok' if seo_score > 95 else 'good'},
                {'name': 'H1 Tag Check', 'value': f'{random_score(70, 100)}% pass', 'status': 'warn' if seo_score < 85 else 'good'},
            ],
        },
        'security': {
            'score': security_score,
            'metrics': [
                {'name': 'SSL/TLS Status', 'value': 'Active', 'status': 'good'},
                {'name': 'Security Headers', 'value': 'Missing CSP' if security_score < 85 else 'All present', 'status': 'critical' if security_score < 85 else 'good'},
                {'name': 'Vulnerability Scan', 'value': 'None Found' if security_score > 95 else 'Low Severity', 'status': 'good' if security_score > 95 else 'warn'},
            ],
        },
        'mobile': {
            'score': mobile_score,
            'metrics': [
                {'name': 'Tap Target Size', 'value': 'Good' if mobile_score > 90 else 'Needs Fix', 'status': 'good' if mobile_score > 90 else 'warn'},
                {'name': 'Viewport Tag', 'value': 'Present', 'status': 'good'},
            ],
        },
        'links': {
            'score': link_score,
            'metrics': [
                {'name': 'Broken Internal Links', 'value': '0' if link_score > 98 else str(random_score(1, 5)), 'status': 'critical' if link_score < 98 else 'good'},
                {'name': 'Broken External Links', 'value': '0', 'status': 'good'},
            ],
        }
    }

    # Add a few issues based on scores
    potential_issues = []
    if perf_score < 70: potential_issues.extend([issues[1], issues[2]])
    if seo_score < 80: potential_issues.append(issues[0])
    if security_score < 85: potential_issues.extend([issues[3], issues[6]])
    if mobile_score < 80: potential_issues.append(issues[5])
    if link_score < 95: potential_issues.append(issues[4])
    
    # Pick 1-4 issues randomly
    issues_found = random.sample(potential_issues, min(random_score(1, 4), len(potential_issues))) if potential_issues else []

    return {
        'timestamp': datetime.now().isoformat(),
        'website_url': url,
        'health_score': health_score,
        'summary': {
            'performance': perf_score,
            'seo': seo_score,
            'security': security_score,
            'mobile': mobile_score,
            'links': link_score,
        },
        'issues_found': issues_found,
        'details': detailed_report,
        'pages_tested_summary': pages_tested_summary, # Added page crawl summary
    }

# --- UI COMPONENTS ---

def display_health_score(score, size=160):
    """Displays the overall health score using Streamlit columns and HTML/CSS for a gauge effect."""
    
    # Simple color logic
    if score >= 70:
        color = "green"
    elif score >= 50:
        color = "orange"
    else:
        color = "red"

    st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; 
                    border: 3px solid #eee; padding: 10px; border-radius: 15px; margin-bottom: 20px;">
            <div style="font-size: 5rem; font-weight: bold; color: {color};">{score}</div>
            <div style="font-size: 1rem; color: #555;">Website Health Score</div>
        </div>
    """, unsafe_allow_html=True)

def display_metric_card(name, score, icon):
    """Displays a single metric card."""
    
    # Simple color logic for metric titles
    if score >= 85:
        color = "green"
    elif score >= 65:
        color = "orange"
    else:
        color = "red"

    st.metric(label=f":{icon}: {name}", value=f"{score}%", help=f"Score out of 100 for {name} metrics.")
    st.progress(score / 100, text=f"**{score}%**")

def display_detailed_report(report):
    """Displays the detailed sectional report."""
    
    sections = [
        {'name': 'Performance', 'icon': 'zap', 'data': report['details']['performance']},
        {'name': 'SEO Health', 'icon': 'search', 'data': report['details']['seo']},
        {'name': 'Security Audit', 'icon': 'lock', 'data': report['details']['security']},
        {'name': 'Mobile Responsiveness', 'icon': 'mobile', 'data': report['details']['mobile']},
        {'name': 'Link Integrity', 'icon': 'link', 'data': report['details']['links']},
    ]

    # Display Crawl/Testing Summary
    st.subheader(":material/public: Crawl & Testing Summary")
    summary = report.get('pages_tested_summary', {})
    
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("Total Pages Tested", summary.get('total_pages', 'N/A'))
    with col_b:
        st.metric("Broken Links", summary.get('broken_links', 'N/A'), delta_color="inverse")
    with col_c:
        st.metric("Missing SEO Data", summary.get('pages_missing_seo', 'N/A'), delta_color="inverse")
    with col_d:
        st.metric("Screenshot Status", "Generated Mock", delta_color="off")
        
    st.markdown("---")
    st.subheader(":material/analytics: Detailed Sectional Analysis")
    
    for section in sections:
        score = section['data']['score']
        
        # Determine title color based on score
        if score >= 85:
            color = "green"
        elif score >= 65:
            color = "orange"
        else:
            color = "red"

        with st.expander(f":{section['icon']}: **{section['name']}** - Score: **{score}%**", expanded=score < 90):
            st.markdown(f"### <span style='color:{color};'>{section['name']} Metrics</span>", unsafe_allow_html=True)
            
            # Convert metrics list to DataFrame for neat display
            metrics_df = pd.DataFrame(section['data']['metrics'])
            
            # Add icon column based on status
            metrics_df['Status Icon'] = metrics_df['status'].apply(lambda s: ":material/check_circle:" if s in ['good', 'ok'] else ":material/error:" if s == 'warn' else ":material/warning:" if s == 'critical' else ":material/schedule:" if s == 'slow' else "")
            
            metrics_df = metrics_df[['Status Icon', 'name', 'value']]
            metrics_df.columns = ['Status', 'Metric Name', 'Value']
            
            st.dataframe(metrics_df, hide_index=True, use_container_width=True)


def main_app():
    """Main Streamlit application logic."""
    st.title("🔥 QA Autopilot Dashboard")
    st.markdown("Automated Website Health Monitoring and QA Testing using Streamlit.")

    # --- INPUT AND TRIGGER ---
    with st.sidebar:
        st.header("New Scan")
        
        # User input for URL
        website_url = st.text_input(
            "Enter Website URL to Scan",
            "https://www.example.com",
            placeholder="e.g., https://www.yourcompany.com"
        )
        
        # Scan button
        run_scan = st.button("Run Automated Scan", type="primary")

        st.markdown("---")
        st.subheader("Email Configuration")
        st.info("You must use an App Password if using Gmail/Outlook, not your main password.")
        
        email_recipient = st.text_input("Recipient Email", "client@example.com")
        email_sender = st.text_input("Sender Email (Your Account)", "your.saas@gmail.com")
        email_password = st.text_input("Sender App Password", type="password")
        
        send_report_button = st.button("Send Report via Email")


    # Initialize session state for reports (simulating history)
    if 'reports' not in st.session_state:
        st.session_state.reports = []

    # --- SCAN LOGIC ---
    if run_scan and website_url:
        
        # 1. Simulate testing process with a spinner/progress bar
        with st.spinner(f"Running comprehensive QA analysis for {website_url} and **{random_score(50, 200)} pages**..."):
            # Simulate API/backend latency
            time.sleep(random_score(2, 4))
            
            # Generate the mock report
            new_report = generate_report_python(website_url)
            
            # Save report to session state (simulates database history)
            st.session_state.reports.insert(0, new_report)

        st.success(f"Scan complete! Report generated for {website_url}.")
        
    # --- EMAIL LOGIC ---
    if send_report_button and st.session_state.reports:
        latest_report = st.session_state.reports[0]
        pdf_content = create_pdf_report(latest_report)
        report_name = f"Report-{latest_report['website_url'].replace('https://', '').replace('/', '_')}"

        if not email_sender or not email_password or not email_recipient:
            st.warning("Please provide Sender Email, App Password, and Recipient Email in the sidebar.")
        else:
            with st.spinner("Sending email report..."):
                # Call the real Python email function
                email_status = send_email_report(email_sender, email_password, email_recipient, report_name, pdf_content)
            
            if email_status == "success":
                st.success(f"✅ Email successfully sent to {email_recipient}!")
            else:
                st.error(f"❌ Failed to send email. Check your SMTP settings and App Password. Error: {email_status}")


    # --- DISPLAY REPORTS ---

    if not st.session_state.reports:
        st.info("No reports available. Enter a URL in the sidebar and click 'Run Automated Scan' to begin monitoring.")
        return

    latest_report = st.session_state.reports[0]
    
    st.header("Latest Website Health Report")
    st.caption(f"Report Generated: {datetime.fromisoformat(latest_report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown(f"### Website: `{latest_report['website_url']}`")
    
    # PDF Download Button
    pdf_content = create_pdf_report(latest_report)
    pdf_filename = f"QA_Report_{latest_report['website_url'].replace('https://', '').replace('/', '_')}.pdf"
    
    st.download_button(
        label="Download PDF Report",
        data=pdf_content.getvalue(),
        file_name=pdf_filename,
        mime="application/pdf"
    )

    # --- Key Metrics Overview ---
    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1, 1, 1, 1, 1])

    with col1:
        display_health_score(latest_report['health_score'])

    with col2:
        display_metric_card("Performance", latest_report['summary']['performance'], "zap")
    
    with col3:
        display_metric_card("SEO Health", latest_report['summary']['seo'], "search")
    
    with col4:
        display_metric_card("Security Audit", latest_report['summary']['security'], "lock")

    with col5:
        display_metric_card("Mobile Resp.", latest_report['summary']['mobile'], "mobile")
        
    with col6:
        display_metric_card("Link Integrity", latest_report['summary']['links'], "link")

    # --- Issues Found ---
    if latest_report['issues_found']:
        st.error("🚨 Critical Issues Found:")
        for issue in latest_report['issues_found']:
            st.markdown(f"- **{issue}**")
    else:
        st.success("✅ No critical issues detected in this run. Great job!")

    st.markdown("---")

    # --- Detailed Analysis and History ---
    tab1, tab2 = st.tabs(["Detailed Analysis", "Scan History"])

    with tab1:
        display_detailed_report(latest_report)

    with tab2:
        st.subheader("Historical Scan Records")
        
        # Prepare data for history table
        history_data = []
        for report in st.session_state.reports:
            history_data.append({
                'Date': datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M'),
                'Health Score': report['health_score'],
                'Performance': f"{report['summary']['performance']}%",
                'SEO': f"{report['summary']['seo']}%",
                'Security': f"{report['summary']['security']}%",
                'Issues': f"{len(report['issues_found'])} Found",
            })
        
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, use_container_width=True, hide_index=True)


if __name__ == '__main__':
    main_app()
