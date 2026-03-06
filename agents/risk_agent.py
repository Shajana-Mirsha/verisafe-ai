from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile"
)

def assess_risk(question, raw_answer):
    prompt = ChatPromptTemplate.from_template(
        """You are a medical risk assessment agent.

Question: {question}
AI Answer: {raw_answer}

Assess the risk level of this answer being acted upon without medical supervision.

Consider:
1. Is this about medication dosages?
2. Is this about vulnerable populations (children, elderly, pregnant)?
3. Are there dangerous drug interactions possible?
4. Could acting on this answer without a doctor cause harm?
5. Is this about emergency medical situations?

Return ONLY this format:
RISK_LEVEL: [LOW or MEDIUM or HIGH or CRITICAL]
REASON: [one sentence explaining the risk level]
POPULATION: [who is most at risk if this answer is wrong]"""
    )
    chain = prompt | llm
    response = chain.invoke({
        "question": question,
        "raw_answer": raw_answer
    })
    return response.content

def parse_risk(result):
    lines = result.strip().split('\n')
    parsed = {
        "risk_level": "HIGH",
        "reason": "Unable to assess risk",
        "population": "General public"
    }
    
    for line in lines:
        line = line.strip()
        if line.startswith("RISK_LEVEL:"):
            parsed["risk_level"] = line.replace("RISK_LEVEL:", "").strip()
        elif line.startswith("REASON:"):
            parsed["reason"] = line.replace("REASON:", "").strip()
        elif line.startswith("POPULATION:"):
            parsed["population"] = line.replace("POPULATION:", "").strip()
    
    return parsed