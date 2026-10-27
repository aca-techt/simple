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

# ------------------- Stronger Glass CSS -------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #e0e7ff 0%, #f0f4ff 40%, #e8f0fe 100%);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        max-width: 720px;
    }
    h1 {
        font-weight: 600;
        letter-spacing: -0.3px;
        color: #1a1a1a;
    }
    .glass {
        background: rgba(255, 255, 255, 0.45);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.7);
        border-radius: 18px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.12);
        margin-bottom: 1.1rem;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        height: 2.7rem;
        background: #0071e3;
        color: white;
        border: none;
    }
    .stButton > button:hover {
        background: #0077ed;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(16px) saturate(160%);
        -webkit-backdrop-filter: blur(16px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.65) !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06);
    }
    .footer {
        text-align: center;
        color: #6e6e73;
        font-size: 0.8rem;
        margin-top: 2.5rem;
    }
    /* Make tabs slightly glassy */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.4);
        border-radius: 12px;
        padding: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------- Header -------------------
st.markdown("<h1 style='text-align:center; margin-bottom:0.1rem;'>Notice Simplifier</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#6e6e73; margin:0 0 1.3rem 0;'>Clear language for official documents</p>", unsafe_allow_html=True)

# ------------------- Examples -------------------
EXAMPLES = {
    "School": """Scholarship Notice
Applications invited from Class 9–12 for National Means-cum-Merit Scholarship.
Last date: 30 November 2026.
Required: Aadhaar, marksheet, income certificate, bank passbook.
Apply on official portal only.""",
    "Municipal": """Public Notice
Water supply in Ward 7 stopped on 18 November 2026 from 9 AM to 5 PM for repairs.
Store water in advance.
Contact ward office between 10 AM and 5 PM.""",
    "Scheme": """PM-KISAN Update
Check installment status on the PM-KISAN portal.
Next payment expected in December 2026.
Ensure Aadhaar and bank account are linked."""
}

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("School", use_container_width=True):
        st.session_state.example = EXAMPLES["School"]
with c2:
    if st.button("Municipal", use_container_width=True):
        st.session_state.example = EXAMPLES["Municipal"]
with c3:
    if st.button("Scheme", use_container_width=True):
        st.session_state.example = EXAMPLES["Scheme"]

# ------------------- Functions -------------------
def extract_text_from_pdf(f):
    text = ""
    with pdfplumber.open(f) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t:
                text += t + "\n"
    return text.strip()

def simplify_document(document, language, doc_type):
    hint = {
        "General": "",
        "School / Education": "Focus on dates, required documents, and eligibility.",
        "Municipal / Local Body": "Focus on dates, affected areas, and actions required.",
        "Government Scheme": "Focus on eligibility, benefits, documents, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite into clear, simple {language}.

{hint}

Use short sentences and everyday words. Do not add information. Do not guess.

**Summary**
(1-2 sentences)

**What to do**
- 

**Important dates**
- 

**Details**
- 

Document:
{document}"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

def answer_question(document, question):
    prompt = f"""Answer only from the document. If not found, reply: "Not mentioned in the document."

Document:
{document}

Question: {question}

Answer:"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

# ------------------- Input Card -------------------
st.markdown('<div class="glass">', unsafe_allow_html=True)

doc_type = st.selectbox("Document type", ["General", "School / Education", "Municipal / Local Body", "Government Scheme"])
language = st.radio("Language", ["Simple English", "Simple Hindi"], horizontal=True)

tab1, tab2 = st.tabs(["Upload", "Paste"])

final_document = st.session_state.get("example", "")

with tab1:
    up = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed")
    if up:
        final_document = extract_text_from_pdf(up) if up.type == "application/pdf" else up.read().decode("utf-8")
        if final_document:
            st.caption(f"Loaded: {up.name}")

with tab2:
    pasted = st.text_area(
        "Paste text",
        value=st.session_state.get("example", ""),
        height=140,
        placeholder="Paste the notice here...",
        label_visibility="collapsed"
    )
    if pasted.strip():
        final_document = pasted.strip()

st.markdown('</div>', unsafe_allow_html=True)

if st.button("Simplify", type="primary", use_container_width=True):
    if not final_document.strip():
        st.error("Please add a document.")
    else:
        with st.spinner("Simplifying..."):
            try:
                result = simplify_document(final_document, language, doc_type)
                st.session_state.doc = final_document
                st.session_state.result = result
                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.insert(0, {"preview": final_document[:90] + "...", "result": result})
                st.session_state.history = st.session_state.history[:3]
            except Exception as e:
                st.error(str(e))

# ------------------- Result -------------------
if "result" in st.session_state:
    st.subheader("Simplified")
    with st.container(border=True):
        st.markdown(st.session_state.result)
    st.download_button(
        "Download",
        st.session_state.result,
        "simplified.txt",
        "text/plain",
        use_container_width=True
    )

# ------------------- Questions -------------------
if "doc" in st.session_state:
    st.write("")
    st.subheader("Ask about this document")
    q = st.text_input("Question", placeholder="What is the deadline? What documents are needed?", label_visibility="collapsed")
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
            st.markdown(h["result"][:200] + "...")

st.markdown('<div class="footer">Always verify with the original document</div>', unsafe_allow_html=True)