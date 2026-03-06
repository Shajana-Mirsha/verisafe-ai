from datetime import datetime

audit_records = []

def add_log(question, verdict, confidence, risk, issues, population):
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question": question[:80] + "..." if len(question) > 80 else question,
        "verdict": verdict,
        "confidence": confidence,
        "risk": risk,
        "issues": issues,
        "population": population
    }
    audit_records.append(record)
    return record

def get_logs():
    return list(reversed(audit_records))