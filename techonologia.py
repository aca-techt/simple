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

st.markdown("""
<style>
    .block-container { padding-top: 1.8rem; padding-bottom: 2rem; max-width: 760px; }
    h1 { font-weight: 600; }
    .stButton > button { border-radius: 8px; font-weight: 500; height: 2.7rem; }
    .note {
        background: #f8f9fa; border: 1px solid #e9ecef;
        padding: 10px 14px; border-radius: 8px; font-size: 0.9rem;
        color: #495057; margin-bottom: 1.2rem;
    }
    .footer { text-align: center; color: #868e96; font-size: 0.8rem; margin-top: 2.5rem; padding-top: 0.8rem; border-top: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; margin-bottom:0.1rem;'>Notice Simplifier</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#6c757d; margin:0 0 1rem 0;'>Clear language for official notices and documents</p>", unsafe_allow_html=True)

st.markdown('<div class="note">Rewrites documents into simpler language. Not official advice — always check the original.</div>', unsafe_allow_html=True)

# ------------------- Examples -------------------
EXAMPLES = {
    "School Notice": """Scholarship Notice
Applications are invited from students of Class 9–12 for the National Means-cum-Merit Scholarship.
Last date: 30 November 2026.
Required: Aadhaar, previous marksheet, income certificate, bank passbook.
Apply on the official portal only. Incomplete forms will be rejected.""",

    "Municipal Notice": """Public Notice – Nagar Palika
Water supply in Ward 7 will be stopped on 18 November 2026 from 9 AM to 5 PM for pipeline repair.
Residents are requested to store water in advance.
For complaints contact the ward office between 10 AM and 5 PM.""",

    "Farmer Scheme": """PM-KISAN Scheme Update
Eligible farmers can check their installment status on the PM-KISAN portal.
Next installment is expected in December 2026.
Ensure your Aadhaar and bank account are linked. Visit the nearest CSC or agriculture office for help."""
}

col_ex1, col_ex2, col_ex3 = st.columns(3)
with col_ex1:
    if st.button("School example", use_container_width=True):
        st.session_state["example"] = EXAMPLES["School Notice"]
with col_ex2:
    if st.button("Municipal example", use_container_width=True):
        st.session_state["example"] = EXAMPLES["Municipal Notice"]
with col_ex3:
    if st.button("Farmer example", use_container_width=True):
        st.session_state["example"] = EXAMPLES["Farmer Scheme"]

# ------------------- Functions -------------------
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()

def simplify_document(document: str, language: str, doc_type: str) -> str:
    type_hint = {
        "General": "",
        "School / Education": "Focus on dates, required documents, and eligibility.",
        "Municipal / Local Body": "Focus on dates, affected areas, and what residents must do.",
        "Government Scheme": "Focus on eligibility, benefits, documents needed, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite the document below into clear, simple {language}.

{type_hint}

Rules:
- Short sentences, everyday words.
- Do not add or invent any information.
- Do not guess.
- Keep it factual and easy to scan.

Structure:
**Summary**
(1–2 sentences)

**What to do**
- (Actions, if any)

**Important dates**
- (Or “None mentioned”)

**Other details**
- (Remaining useful points)

Document:
{document}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

def answer_question(document: str, question: str) -> str:
    prompt = f"""Answer using only the document. If not present, say exactly: "Not mentioned in the document."

Document:
{document}

Question: {question}

Answer:"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

# ------------------- Input -------------------
doc_type = st.selectbox(
    "Document type (optional)",
    ["General", "School / Education", "Municipal / Local Body", "Government Scheme"]
)

language = st.radio("Language", ["Simple English", "Simple Hindi"], horizontal=True)

tab1, tab2 = st.tabs(["Upload", "Paste"])

final_document = st.session_state.get("example", "")

with tab1:
    uploaded = st.file_uploader("PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed")
    if uploaded:
        if uploaded.type == "application/pdf":
            final_document = extract_text_from_pdf(uploaded)
        else:
            final_document = uploaded.read().decode("utf-8")
        if final_document:
            st.success(f"Loaded {uploaded.name}")

with tab2:
    pasted = st.text_area(
        "Text",
        value=st.session_state.get("example", ""),
        height=150,
        placeholder="Paste document here...",
        label_visibility="collapsed"
    )
    if pasted.strip():
        final_document = pasted.strip()

if final_document and len(final_document) > 12000:
    st.warning("Long document — may take longer.")

if st.button("Simplify", type="primary", use_container_width=True):
    if not final_document.strip():
        st.error("Add a document first.")
    else:
        with st.spinner("Simplifying..."):
            try:
                result = simplify_document(final_document, language, doc_type)
                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.insert(0, {
                    "preview": final_document[:90] + "...",
                    "result": result,
                    "type": doc_type
                })
                st.session_state.history = st.session_state.history[:3]
                st.session_state["doc"] = final_document
                st.session_state["result"] = result
            except Exception as e:
                st.error(str(e))

# ------------------- Result + Download -------------------
if "result" in st.session_state:
    st.subheader("Simplified")
    with st.container(border=True):
        st.markdown(st.session_state["result"])

    st.download_button(
        label="Download as text",
        data=st.session_state["result"],
        file_name="simplified_notice.txt",
        mime="text/plain",
        use_container_width=True
    )

# ------------------- Questions -------------------
if "doc" in st.session_state:
    st.divider()
    st.subheader("Ask about this document")
    q = st.text_input("Question", placeholder="Deadline? Documents needed? Who to contact?", label_visibility="collapsed")
    if st.button("Answer", use_container_width=True) and q:
        with st.spinner("Checking document..."):
            try:
                ans = answer_question(st.session_state["doc"], q)
                with st.container(border=True):
                    st.markdown(ans)
            except Exception as e:
                st.error(str(e))

# ------------------- History -------------------
if st.session_state.get("history"):
    with st.expander("Recent"):
        for h in st.session_state.history:
            st.caption(f"{h['type']} — {h['preview']}")
            st.markdown(h["result"][:220] + "...")
            st.divider()

st.markdown('<div class="footer">For clearer reading of official documents • Always verify the original</div>', unsafe_allow_html=True)