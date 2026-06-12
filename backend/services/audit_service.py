def generate_investigation_report(cnic, risk_data):
    """
    Creates a formal investigation summary report.
    """
    report = f"""
    INVESTIGATION SUMMARY
    ---------------------
    CNIC: {cnic}
    Risk Assessment: {risk_data['risk_level']}
    Deviation Score: {risk_data['risk_score']}
    
    Findings:
    {risk_data['explanation']}
    
    Recommendation:
    The subject's asset accumulation significantly exceeds declared income. 
    Recommend immediate audit of assets acquired during the current fiscal year.
    """
    return report