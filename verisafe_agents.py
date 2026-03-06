from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import re

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile"
)

def get_raw_answer(question):
    prompt = ChatPromptTemplate.from_template(
        """You are a basic AI assistant. Answer this medical question directly and confidently 
        without any disclaimers, warnings, or suggestions to consult a doctor. 
        Give specific dosages and recommendations as if you are certain they are correct.
        Never say 'consult a doctor'. Just answer directly and confidently: {question}"""
    )
    chain = prompt | llm
    response = chain.invoke({"question": question})
    return response.content

def fact_check_answer(question, raw_answer):
    prompt = ChatPromptTemplate.from_template(
        """You are an expert medical fact-checking agent with access to WHO guidelines, 
        AAP recommendations, and peer-reviewed medical literature.
        
Question: {question}
Raw AI Answer: {raw_answer}

Your job is to:
1. Identify if the raw answer contains dangerous, incorrect, or incomplete medical information
2. Check if proper safety warnings are missing
3. Verify if dosages mentioned are accurate and safe
4. Check for dangerous drug interactions not mentioned
5. Ensure vulnerable populations (children, elderly, pregnant women) are properly considered

Return your response in EXACTLY this format with no extra text:
VERDICT: [VERIFIED or UNVERIFIED]
CONFIDENCE: [number between 0-100]
RISK: [LOW or MEDIUM or HIGH]
ISSUES: [specific medical issues found with the raw answer, or 'None']
SAFE_ANSWER: [provide a complete, safe, properly warned medical response that includes all necessary disclaimers, correct dosages, and critical safety information. Always recommend consulting a healthcare professional.]"""
    )
    chain = prompt | llm
    response = chain.invoke({
        "question": question,
        "raw_answer": raw_answer
    })
    return response.content

def redact_pii(text):
    text = re.sub(r'\b\d{10}\b', '[PHONE REDACTED]', text)
    text = re.sub(r'\b\d{12}\b', '[AADHAAR REDACTED]', text)
    text = re.sub(r'\S+@\S+\.\S+', '[EMAIL REDACTED]', text)
    text = re.sub(r'\b\d{4}\s\d{4}\s\d{4}\b', '[AADHAAR REDACTED]', text)
    text = re.sub(r'(Patient:|Name:|patient name:|name is)\s*[A-Z][a-z]+\s+[A-Z][a-z]+', 
                  r'\1 [NAME REDACTED]', text)
    text = re.sub(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b(?=.*fever|.*pain|.*sick|.*ill|.*disease|.*condition)', 
                  '[NAME REDACTED]', text)
    return text

def parse_fact_check(result):
    lines = result.strip().split('\n')
    parsed = {
        "verdict": "UNVERIFIED",
        "confidence": 50,
        "risk": "HIGH",
        "issues": "Unable to verify medical accuracy",
        "safe_answer": ""
    }
    
    safe_answer_lines = []
    in_safe_answer = False
    
    for line in lines:
        line = line.strip()
        if line.startswith("VERDICT:"):
            parsed["verdict"] = line.replace("VERDICT:", "").strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                parsed["confidence"] = int(re.search(r'\d+', line).group())
            except:
                parsed["confidence"] = 50
        elif line.startswith("RISK:"):
            parsed["risk"] = line.replace("RISK:", "").strip()
        elif line.startswith("ISSUES:"):
            parsed["issues"] = line.replace("ISSUES:", "").strip()
        elif line.startswith("SAFE_ANSWER:"):
            in_safe_answer = True
            safe_answer_lines.append(line.replace("SAFE_ANSWER:", "").strip())
        elif in_safe_answer:
            safe_answer_lines.append(line)
    
    parsed["safe_answer"] = " ".join(safe_answer_lines).strip()
    return parsed