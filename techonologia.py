import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import pdfplumber

# ------------------- Setup -------------------
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"

st.set_page_config(
    page_title="Notice Simplifier",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ------------------- Glass-style CSS -------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f5f7fa 0%, #e8ecf1 100%);
    }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 2.5rem;
        max-width: 720px;
    }
    h1 {
        font-weight: 600;
        letter-spacing: -0.4px;
        color: #1d1d1f;
    }
    .glass {
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 16px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
        margin-bottom: 1rem;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        height: 2.65rem;
        border: none;
        background: #007aff;
        color: white;
    }
    .stButton > button:hover {
        background: #0066d6;
    }
    .secondary-btn > button {
        background: rgba(255,255,255,0.8) !important;
        color: #1d1d1f !important;
        border: 1px solid #d2d2d7 !important;
    }
    .footer {
        text-align: center;
        color: #86868b;
        font-size: 0.8rem;
        margin-top: 2.8rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.65);
        backdrop-filter: blur(12px);
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.6);
    }
</style>
""", unsafe_allow_html=True)

# ------------------- Header -------------------
st.markdown("<h1 style='text-align:center; margin-bottom:0.15rem;'>Notice Simplifier</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#86868b; margin:0 0 1.4rem 0; font-size:0.95rem;'>Clear language for official documents</p>", unsafe_allow_html=True)

# ------------------- Examples -------------------
EXAMPLES = {
    "School": """Scholarship Notice
Applications invited from Class 9–12 students for National Means-cum-Merit Scholarship.
Last date: 30 November 2026.
Required: Aadhaar, marksheet, income certificate, bank passbook.
Apply on official portal only.""",

    "Municipal": """Public Notice
Water supply in Ward 7 stopped on 18 November 2026, 9 AM–5 PM for repairs.
Store water in advance.
Contact ward office 10 AM–5 PM for issues.""",

    "Scheme": """PM-KISAN Update
Check installment status on PM-KISAN portal.
Next payment expected December 2026.
Link Aadhaar and bank account. Visit CSC or agriculture office if needed."""
}

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("School", use_container_width=True, key="ex1"):
        st.session_state.example = EXAMPLES["School"]
with c2:
    if st.button("Municipal", use_container_width=True, key="ex2"):
        st.session_state.example = EXAMPLES["Municipal"]
with c3:
    if st.button("Scheme", use_container_width=True, key="ex3"):
        st.session_state.example = EXAMPLES["Scheme"]

# ------------------- Functions -------------------
def extract_text_from_pdf(f):
    text = ""
    with pdfplumber.open(f) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t: text += t + "\n"
    return text.strip()

def simplify_document(document, language, doc_type):
    hint = {
        "General": "",
        "School / Education": "Emphasize dates, documents, and eligibility.",
        "Municipal / Local Body": "Emphasize dates, areas affected, and required actions.",
        "Government Scheme": "Emphasize eligibility, benefits, documents, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite into clear, simple {language}.

{hint}

Rules: short sentences, everyday words, no added information, no guessing.

**Summary**
(1-2 sentences)

**What to do**
- actions if any

**Important dates**
- or none

**Details**
- other points

Document:
{document}"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

def answer_question(document, question):
    prompt = f"""Answer only from the document. If absent: "Not mentioned in the document."

Document:
{document}

Question: {question}

Answer:"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

# ------------------- Input -------------------
st.markdown('<div class="glass">', unsafe_allow_html=True)

doc_type = st.selectbox("Type", ["General", "School / Education", "Municipal / Local Body", "Government Scheme"], label_visibility="collapsed")
language = st.radio("Language", ["Simple English", "Simple Hindi"], horizontal=True, label_visibility="collapsed")

tab1, tab2 = st.tabs(["Upload", "Paste"])

final_document = st.session_state.get("example", "")

with tab1:
    up = st.file_uploader("File", type=["pdf", "txt"], label_visibility="collapsed")
    if up:
        final_document = extract_text_from_pdf(up) if up.type == "application/pdf" else up.read().decode("utf-8")
        if final_document:
            st.caption(f"Loaded {up.name}")

with tab2:
    pasted = st.text_area("Text", value=st.session_state.get("example", ""), height=140, placeholder="Paste here...", label_visibility="collapsed")
    if pasted.strip():
        final_document = pasted.strip()

st.markdown('</div>', unsafe_allow_html=True)

if st.button("Simplify", type="primary", use_container_width=True):
    if not final_document.strip():
        st.error("Add a document.")
    else:
        with st.spinner("Simplifying..."):
            try:
                result = simplify_document(final_document, language, doc_type)
                st.session_state.doc = final_document
                st.session_state.result = result
                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.insert(0, {"preview": final_document[:80]+"...", "result": result})
                st.session_state.history = st.session_state.history[:3]
            except Exception as e:
                st.error(str(e))

# ------------------- Result -------------------
if "result" in st.session_state:
    st.subheader("Simplified")
    with st.container(border=True):
        st.markdown(st.session_state.result)
    st.download_button("Download", st.session_state.result, "simplified.txt", "text/plain", use_container_width=True)

# ------------------- Q&A -------------------
if "doc" in st.session_state:
    st.write("")
    st.subheader("Ask")
    q = st.text_input("Q", placeholder="Deadline? Documents? Contact?", label_visibility="collapsed")
    if st.button("Answer", use_container_width=True) and q:
        with st.spinner("Checking..."):
            try:
                ans = answer_question(st.session_state.doc, q)
                with st.container(border=True):
                    st.markdown(ans)
            except Exception as e:
                st.error(str(e))

# ------------------- History -------------------
if st.session_state.get("history"):
    with st.expander("Recent"):
        for h in st.session_state.history:
            st.caption(h["preview"])
            st.markdown(h["result"][:180] + "...")

st.markdown('<div class="footer">Always verify with the original document</div>', unsafe_allow_html=True)