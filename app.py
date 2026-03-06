import streamlit as st
import time
from agents.fact_check import get_raw_answer, fact_check_answer
from agents.risk_agent import assess_risk, parse_risk
from agents.confidence import calculate_confidence
from agents.pii_redactor import redact_pii
from utils.audit_log import add_log, get_logs
from datetime import datetime
import re

# Page config
st.set_page_config(
    page_title="VeriSafe AI",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {background-color: #0a0a0a;}
    .stApp {background-color: #0a0a0a;}
    
    .header-box {
        background: linear-gradient(135deg, #0d2e1a, #1a4d2e);
        border: 2px solid #00ff88;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .verified {
        background-color: #0d2e1a;
        border: 2px solid #00ff88;
        border-radius: 10px;
        padding: 20px;
        color: #00ff88;
        margin: 10px 0;
    }
    
    .unverified {
        background-color: #2e0d0d;
        border: 2px solid #ff4444;
        border-radius: 10px;
        padding: 20px;
        color: #ff4444;
        margin: 10px 0;
    }
    
    .warning-box {
        background-color: #2e1f0d;
        border: 2px solid #ffaa00;
        border-radius: 10px;
        padding: 20px;
        color: #ffaa00;
        margin: 10px 0;
    }
    
    .agent-box {
        background-color: #111;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        margin: 5px 0;
        color: white;
    }
    
    .agent-active {
        background-color: #0d1a2e;
        border: 1px solid #0088ff;
        border-radius: 8px;
        padding: 15px;
        margin: 5px 0;
        color: #0088ff;
    }
    
    .stat-box {
        background-color: #111;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        color: white;
    }
    
    .reasoning-box {
        background-color: #0d0d1a;
        border: 1px solid #4444ff;
        border-radius: 10px;
        padding: 20px;
        color: #aaaaff;
        margin: 10px 0;
    }
    
    .audit-entry {
        background-color: #111;
        border-left: 4px solid #333;
        border-radius: 5px;
        padding: 10px 15px;
        margin: 5px 0;
        color: white;
        font-size: 14px;
    }
    
    .pii-box {
        background-color: #1a1a0d;
        border: 2px solid #ffff00;
        border-radius: 10px;
        padding: 15px;
        color: #ffff00;
        margin: 10px 0;
    }
    
    h1, h2, h3 {color: white !important;}
    p {color: #cccccc;}
    
    .stTextArea textarea {
        background-color: #111 !important;
        color: white !important;
        border: 1px solid #333 !important;
        font-size: 16px !important;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #00ff88, #00aa55) !important;
        color: black !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 15px !important;
    }

    .confidence-high { color: #00ff88; font-size: 24px; font-weight: bold; }
    .confidence-med { color: #ffaa00; font-size: 24px; font-weight: bold; }
    .confidence-low { color: #ff4444; font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-box">
    <h1 style="color: #00ff88; font-size: 48px; margin: 0;">🛡️ VeriSafe AI</h1>
    <p style="color: #aaaaaa; font-size: 18px; margin-top: 10px;">
        Real-time Hallucination Detection & AI Verification for Healthcare
    </p>
    <p style="color: #666666; font-size: 14px;">
        Powered by Multi-Agent Validation Engine | Built for Safe AI Deployment
    </p>
</div>
""", unsafe_allow_html=True)

# Session state
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []
if "total" not in st.session_state:
    st.session_state.total = 0
if "verified_count" not in st.session_state:
    st.session_state.verified_count = 0
if "flagged_count" not in st.session_state:
    st.session_state.flagged_count = 0
if "pii_count" not in st.session_state:
    st.session_state.pii_count = 0

# Stats Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-box">
        <h2 style="color: #0088ff;">{st.session_state.total}</h2>
        <p>Total Queries</p>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="stat-box">
        <h2 style="color: #00ff88;">{st.session_state.verified_count}</h2>
        <p>✅ Verified Safe</p>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="stat-box">
        <h2 style="color: #ff4444;">{st.session_state.flagged_count}</h2>
        <p>⚠️ Flagged</p>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="stat-box">
        <h2 style="color: #ffff00;">{st.session_state.pii_count}</h2>
        <p>🔒 PII Blocked</p>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# Input Section
st.markdown("<h3 style='color: white;'>💬 Ask a Medical Question</h3>", unsafe_allow_html=True)
st.markdown("<p style='color: #888;'>Type any medical question. VeriSafe will validate it through 3 AI agents before showing you a safe, verified response.</p>", unsafe_allow_html=True)

question = st.text_area(
    "",
    placeholder="Example: Can I give 500mg of aspirin to a 2 year old child for fever?",
    height=120,
    key="question_input"
)

verify_button = st.button("🛡️ VERIFY WITH VERISAFE", use_container_width=True)

st.markdown("---")

if verify_button and question.strip():

    # PII Check
    clean_question = redact_pii(question)
    if clean_question != question:
        st.session_state.pii_count += 1
        st.markdown(f"""
        <div class="pii-box">
            🔒 <b>PII DETECTED & AUTOMATICALLY REDACTED</b><br><br>
            Personal information has been removed to protect patient privacy.<br><br>
            <b>Cleaned Query:</b> {clean_question}
        </div>""", unsafe_allow_html=True)

    # Step 1 - Raw AI Response
    st.markdown("<h3 style='color: #ff4444;'>⚠️ STEP 1: Raw AI Response (Unverified)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888;'>This is what a standard AI would show you directly — with no safety checks.</p>", unsafe_allow_html=True)

    with st.spinner("Getting raw AI response..."):
        raw_answer = get_raw_answer(clean_question)

    st.markdown(f"""
    <div class="unverified">
        ⚠️ <b>UNVERIFIED — NOT SAFE TO ACT ON</b><br><br>
        {raw_answer}
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Step 2 - Agent Processing
    st.markdown("<h3 style='color: #0088ff;'>🔄 STEP 2: VeriSafe Multi-Agent Validation Engine</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888;'>Three independent AI agents now cross-check this response.</p>", unsafe_allow_html=True)

    # Agent 1 - Fact Check
    agent1_placeholder = st.empty()
    agent1_placeholder.markdown("""
    <div class="agent-active">
        🔍 <b>Agent 1 — Fact-Check Agent</b> | Scanning WHO guidelines and medical knowledge base...
    </div>""", unsafe_allow_html=True)

    with st.spinner(""):
        fact_result = fact_check_answer(clean_question, raw_answer)
        time.sleep(0.5)

    agent1_placeholder.markdown("""
    <div class="agent-box">
        ✅ <b>Agent 1 — Fact-Check Agent</b> | Analysis complete
    </div>""", unsafe_allow_html=True)

    # Agent 2 - Risk Assessment
    agent2_placeholder = st.empty()
    agent2_placeholder.markdown("""
    <div class="agent-active">
        ⚖️ <b>Agent 2 — Risk & Bias Agent</b> | Evaluating danger level and population risk...
    </div>""", unsafe_allow_html=True)

    with st.spinner(""):
        risk_result = assess_risk(clean_question, raw_answer)
        parsed_risk = parse_risk(risk_result)
        time.sleep(0.5)

    agent2_placeholder.markdown(f"""
    <div class="agent-box">
        ✅ <b>Agent 2 — Risk & Bias Agent</b> | Risk Level: {parsed_risk['risk_level']} | Population at risk: {parsed_risk['population']}
    </div>""", unsafe_allow_html=True)

    # Agent 3 - Confidence Score
    agent3_placeholder = st.empty()
    agent3_placeholder.markdown("""
    <div class="agent-active">
        📊 <b>Agent 3 — Confidence Scoring Agent</b> | Calculating reliability score...
    </div>""", unsafe_allow_html=True)

    with st.spinner(""):
        confidence_score, confidence_reasoning = calculate_confidence(
            clean_question, raw_answer, parsed_risk['risk_level']
        )
        time.sleep(0.5)

    agent3_placeholder.markdown(f"""
    <div class="agent-box">
        ✅ <b>Agent 3 — Confidence Scoring Agent</b> | Score: {confidence_score}% | {confidence_reasoning}
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Parse fact check result
    def parse_fact_check(result):
        lines = result.strip().split('\n')
        parsed = {
            "verdict": "UNVERIFIED",
            "issues": "Unable to verify",
            "safe_answer": ""
        }
        safe_answer_lines = []
        in_safe_answer = False
        for line in lines:
            line = line.strip()
            if line.startswith("VERDICT:"):
                parsed["verdict"] = line.replace("VERDICT:", "").strip()
            elif line.startswith("ISSUES:"):
                parsed["issues"] = line.replace("ISSUES:", "").strip()
            elif line.startswith("SAFE_ANSWER:"):
                in_safe_answer = True
                safe_answer_lines.append(line.replace("SAFE_ANSWER:", "").strip())
            elif in_safe_answer:
                safe_answer_lines.append(line)
        parsed["safe_answer"] = " ".join(safe_answer_lines).strip()
        return parsed

    parsed = parse_fact_check(fact_result)
    verdict = parsed["verdict"]
    issues = parsed["issues"]
    safe_answer = parsed["safe_answer"]

    # Step 3 - Verified Output
    st.markdown("<h3 style='color: #00ff88;'>🛡️ STEP 3: VeriSafe Verified Output</h3>", unsafe_allow_html=True)

    # Confidence display
    if confidence_score >= 80:
        conf_class = "confidence-high"
        conf_emoji = "🟢"
    elif confidence_score >= 60:
        conf_class = "confidence-med"
        conf_emoji = "🟡"
    else:
        conf_class = "confidence-low"
        conf_emoji = "🔴"

    col_v, col_c, col_r = st.columns(3)
    with col_v:
        verdict_color = "#00ff88" if verdict == "VERIFIED" else "#ff4444"
        st.markdown(f"""
        <div class="stat-box">
            <h2 style="color: {verdict_color};">{verdict}</h2>
            <p>Final Verdict</p>
        </div>""", unsafe_allow_html=True)
    with col_c:
        st.markdown(f"""
        <div class="stat-box">
            <h2 class="{conf_class}">{conf_emoji} {confidence_score}%</h2>
            <p>Confidence Score</p>
        </div>""", unsafe_allow_html=True)
    with col_r:
        risk_colors = {"LOW": "#00ff88", "MEDIUM": "#ffaa00", "HIGH": "#ff4444", "CRITICAL": "#ff0000"}
        risk_color = risk_colors.get(parsed_risk['risk_level'], "#ff4444")
        st.markdown(f"""
        <div class="stat-box">
            <h2 style="color: {risk_color};">{parsed_risk['risk_level']}</h2>
            <p>Risk Level</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if verdict == "VERIFIED":
        st.markdown(f"""
        <div class="verified">
            ✅ <b>VERIFIED & SAFE TO REFERENCE</b><br><br>
            {safe_answer}<br><br>
            <small>📚 <b>Source:</b> WHO Essential Medicines Guidelines | AAP Recommendations | Medical Knowledge Base</small>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="unverified">
            ❌ <b>FLAGGED — DO NOT ACT WITHOUT CONSULTING A DOCTOR</b><br><br>
            {safe_answer}<br><br>
            <small>⚠️ <b>Issues Found:</b> {issues}</small><br>
            <small>👥 <b>Population at Risk:</b> {parsed_risk['population']}</small>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Reasoning Path
    st.markdown("<h3 style='color: #4444ff;'>🧠 Transparent Reasoning Path</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888;'>Every decision VeriSafe makes is fully explainable. No black box.</p>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="reasoning-box">
        <b>Step 1:</b> Query received ✅<br>
        <b>Step 2:</b> PII scan completed — {'PII detected and redacted 🔒' if clean_question != question else 'No PII found ✅'}<br>
        <b>Step 3:</b> Raw AI response generated ✅<br>
        <b>Step 4:</b> Fact-Check Agent cross-referenced WHO guidelines ✅<br>
        <b>Step 5:</b> Risk Agent assessed danger level → {parsed_risk['risk_level']} risk | Reason: {parsed_risk['reason']} ✅<br>
        <b>Step 6:</b> Confidence Agent calculated reliability → {confidence_score}% | {confidence_reasoning} ✅<br>
        <b>Step 7:</b> Final verdict determined → {verdict} ✅<br>
        <b>Step 8:</b> Audit log entry created with timestamp ✅
    </div>""", unsafe_allow_html=True)

    # Update session stats
    st.session_state.total += 1
    if verdict == "VERIFIED":
        st.session_state.verified_count += 1
    else:
        st.session_state.flagged_count += 1

    # Add to audit log
    st.session_state.audit_log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "question": clean_question[:60] + "..." if len(clean_question) > 60 else clean_question,
        "verdict": verdict,
        "confidence": confidence_score,
        "risk": parsed_risk['risk_level'],
        "issues": issues,
        "population": parsed_risk['population']
    })

    st.markdown("---")

elif verify_button and not question.strip():
    st.warning("Please enter a medical question first.")

# Audit Log
st.markdown("<h3 style='color: white;'>📋 Live Audit Log</h3>", unsafe_allow_html=True)
st.markdown("<p style='color: #888;'>Every query is logged with full transparency for compliance and review.</p>", unsafe_allow_html=True)

if st.session_state.audit_log:
    for log in reversed(st.session_state.audit_log):
        color = "#00ff88" if log["verdict"] == "VERIFIED" else "#ff4444"
        st.markdown(f"""
        <div class="audit-entry" style="border-left-color: {color};">
            🕐 <b>{log["time"]}</b> |
            <span style="color:{color}"><b>{log["verdict"]}</b></span> |
            Confidence: <b>{log["confidence"]}%</b> |
            Risk: <b>{log["risk"]}</b> |
            Population: {log["population"]} |
            Query: <i>{log["question"]}</i>
        </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="agent-box">
        No queries yet. Ask a medical question above to begin.
    </div>""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<p style='text-align: center; color: #444;'>
    VeriSafe AI — Making AI Safe for Healthcare | 
    Powered by Multi-Agent Validation | 
    Built for Astrava Hackathon 2026
</p>""", unsafe_allow_html=True)