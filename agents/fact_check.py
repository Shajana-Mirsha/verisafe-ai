from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

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
SAFE_ANSWER: [provide a complete, safe, properly warned medical response that includes 
all necessary disclaimers, correct dosages, and critical safety information. 
Always recommend consulting a healthcare professional.]"""
    )
    chain = prompt | llm
    response = chain.invoke({
        "question": question,
        "raw_answer": raw_answer
    })
    return response.content