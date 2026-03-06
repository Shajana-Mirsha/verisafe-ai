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

def calculate_confidence(question, raw_answer, risk_level):
    prompt = ChatPromptTemplate.from_template(
        """You are a medical confidence scoring agent.

Question: {question}
AI Answer: {raw_answer}
Risk Level: {risk_level}

Calculate a confidence score for this answer being medically accurate and safe.

Consider:
1. Is the answer based on well established medical guidelines?
2. Are dosages specific and verifiable?
3. Are safety warnings included?
4. Is the risk level high or critical?
5. Could this answer vary significantly by individual patient factors?

Rules:
- If risk is CRITICAL: confidence maximum is 40
- If risk is HIGH: confidence maximum is 65
- If risk is MEDIUM: confidence maximum is 80
- If risk is LOW: confidence can be up to 98
- Deduct points for missing disclaimers
- Deduct points for missing source citations
- Deduct points for overly specific dosages without patient context

Return ONLY this format:
CONFIDENCE_SCORE: [number between 0-100]
REASONING: [one sentence explaining the score]"""
    )
    chain = prompt | llm
    response = chain.invoke({
        "question": question,
        "raw_answer": raw_answer,
        "risk_level": risk_level
    })
    
    lines = response.content.strip().split('\n')
    score = 50
    reasoning = "Unable to calculate confidence"
    
    for line in lines:
        line = line.strip()
        if line.startswith("CONFIDENCE_SCORE:"):
            try:
                score = int(re.search(r'\d+', line).group())
            except:
                score = 50
        elif line.startswith("REASONING:"):
            reasoning = line.replace("REASONING:", "").strip()
    
    return score, reasoning