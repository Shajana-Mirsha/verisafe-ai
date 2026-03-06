import re

def redact_pii(text):
    # Redact phone numbers
    text = re.sub(r'\b\d{10}\b', '[PHONE REDACTED]', text)
    
    # Redact Aadhaar numbers
    text = re.sub(r'\b\d{12}\b', '[AADHAAR REDACTED]', text)
    
    # Redact email addresses
    text = re.sub(r'\S+@\S+\.\S+', '[EMAIL REDACTED]', text)
    
    # Redact Aadhaar with spaces
    text = re.sub(r'\b\d{4}\s\d{4}\s\d{4}\b', '[AADHAAR REDACTED]', text)
    
    # Redact patient names after keywords
    text = re.sub(
        r'(Patient:|Name:|patient name:|name is)\s*[A-Z][a-z]+\s+[A-Z][a-z]+',
        r'\1 [NAME REDACTED]',
        text
    )
    
    return text