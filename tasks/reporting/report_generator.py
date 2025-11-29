def calculate_quality_score(raw_results):
    """
    Calculates a final overall quality score based on check results.
    """
    score = 100
    details = []

    # Check 1: HTTP Status (Worth 40 points)
    if raw_results['http_status']['status'] == 'FAIL':
        score -= 40
        details.append("Major deduction: Non-2xx HTTP status code.")
    elif raw_results['http_status']['response_time'] > 5.0:
        score -= 10
        details.append(f"Minor deduction: Slow response time ({raw_results['http_status']['response_time']}s).")
    
    # Check 2: SEO Tags (Worth 30 points)
    if raw_results['seo_tags']['status'] == 'FAIL':
        score -= 30
        details.append("Major deduction: Missing or too-short page title.")
    elif not raw_results['seo_tags']['desc_present']:
        score -= 10
        details.append("Minor deduction: Missing meta description.")
        
    final_score = max(0, score)
    
    return {
        'score': final_score,
        'summary': details,
        'total_checks': 2
    }

def generate_report_summary(raw_results):
    """
    Generates the final structured report to be displayed to the user.
    """
    score_data = calculate_quality_score(raw_results)
    
    report = {
        'url': raw_results['url'],
        'overall_score': score_data['score'],
        'detailed_breakdown': {
            'http_status': raw_results['http_status'],
            'seo_tags': raw_results['seo_tags']
        },
        'summary': score_data['summary'],
        'timestamp': raw_results['timestamp']
    }
    
    return report
