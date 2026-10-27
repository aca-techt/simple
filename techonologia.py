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

# ------------------- App-like CSS -------------------
st.markdown("""
<style>
    .stApp {
        background-color: #f7f8fa;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 680px;
    }
    h1 {
        font-size: 1.75rem;
        font-weight: 600;
        color: #111;
        margin-bottom: 0.25rem;
    }
    .app-header {
        background: white;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 1.25rem;
    }
    .card {
        background: white;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    .stButton > button[kind="primary"] {
        background-color: #111;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #333;
    }
    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.8rem;
        margin-top: 2rem;
        padding-top: 1rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# ------------------- Header -------------------
st.markdown('<div class="app-header">', unsafe_allow_html=True)
st.title("Notice Simplifier")
st.caption("Turn official notices and documents into clear, simple language")
st.markdown('</div>', unsafe_allow_html=True)

# ------------------- Examples -------------------
EXAMPLES = {
    "School": """Scholarship Notice
Applications are invited from students of Class 9 to 12 for the National Means-cum-Merit Scholarship.
Last date to apply: 30 November 2026.
Required documents: Aadhaar card, previous year marksheet, income certificate, and bank passbook.
Apply only through the official portal.""",

    "Municipal": """Public Notice
Water supply in Ward 7 will be suspended on 18 November 2026 from 9:00 AM to 5:00 PM due to pipeline repairs.
Residents should store water in advance.
Contact the ward office between 10:00 AM and 5:00 PM for assistance.""",

    "Scheme": """PM-KISAN Scheme
Eligible farmers can check their installment status on the official PM-KISAN portal.
The next installment is expected in December 2026.
Ensure your Aadhaar and bank account details are correctly linked."""
}

st.markdown('<div class="card">', unsafe_allow_html=True)
st.write("**Quick examples**")
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
st.markdown('</div>', unsafe_allow_html=True)

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
    focus = {
        "General": "",
        "School / Education": "Focus on dates, required documents, and who is eligible.",
        "Municipal / Local Body": "Focus on dates, affected areas, and what people need to do.",
        "Government Scheme": "Focus on eligibility, benefits, documents needed, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite this document into clear, simple {language}.

{focus}

Rules:
- Short sentences and everyday words only.
- Do not add or invent any information.
- Do not guess.

Format exactly like this:

**Summary**
(1-2 sentences)

**What to do**
- (actions, or "None")

**Important dates**
- (dates, or "None mentioned")

**Other details**
- (remaining points)

Document:
{document}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

def answer_question(document: str, question: str) -> str:
    prompt = f"""Answer the question using only the document below.
If the information is not in the document, reply exactly: "Not mentioned in the document."

Document:
{document}

Question: {question}

Answer:"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

# ------------------- Input Card -------------------
st.markdown('<div class="card">', unsafe_allow_html=True)

doc_type = st.selectbox(
    "Document type",
    ["General", "School / Education", "Municipal / Local Body", "Government Scheme"]
)

language = st.radio("Language", ["Simple English", "Simple Hindi"], horizontal=True)

tab1, tab2 = st.tabs(["Upload file", "Paste text"])

final_document = st.session_state.get("example", "")

with tab1:
    uploaded = st.file_uploader("PDF or TXT file", type=["pdf", "txt"], label_visibility="collapsed")
    if uploaded:
        if uploaded.type == "application/pdf":
            final_document = extract_text_from_pdf(uploaded)
        else:
            final_document = uploaded.read().decode("utf-8")
        if final_document:
            st.success(f"File loaded: {uploaded.name}")

with tab2:
    pasted = st.text_area(
        "Document text",
        value=st.session_state.get("example", ""),
        height=150,
        placeholder="Paste the notice or document here...",
        label_visibility="collapsed"
    )
    if pasted.strip():
        final_document = pasted.strip()

if final_document and len(final_document) > 10000:
    st.caption("Long document — this may take a few extra seconds.")

st.markdown('</div>', unsafe_allow_html=True)

if st.button("Simplify document", type="primary", use_container_width=True):
    if not final_document.strip():
        st.error("Please upload a file or paste text first.")
    else:
        with st.spinner("Simplifying..."):
            try:
                result = simplify_document(final_document, language, doc_type)
                st.session_state.doc = final_document
                st.session_state.result = result
                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.insert(0, {
                    "preview": final_document[:90] + "...",
                    "result": result,
                    "type": doc_type
                })
                st.session_state.history = st.session_state.history[:3]
            except Exception as e:
                st.error(str(e))

# ------------------- Result -------------------
if "result" in st.session_state:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Simplified")
    st.markdown(st.session_state.result)
    st.download_button(
        "Download text",
        data=st.session_state.result,
        file_name="simplified.txt",
        mime="text/plain",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------- Questions -------------------
if "doc" in st.session_state:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Ask about this document")
    question = st.text_input(
        "Question",
        placeholder="What is the deadline? What documents are needed?",
        label_visibility="collapsed"
    )
    if st.button("Get answer", use_container_width=True) and question:
        with st.spinner("Checking the document..."):
            try:
                answer = answer_question(st.session_state.doc, question)
                st.write(answer)
            except Exception as e:
                st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------- History -------------------
if st.session_state.get("history"):
    with st.expander("Recent"):
        for item in st.session_state.history:
            st.write(f"**{item['type']}**")
            st.caption(item["preview"])
            st.write(item["result"][:180] + "...")
            st.divider()

# ------------------- Footer -------------------
st.markdown('<div class="footer">Always verify important details with the original document</div>', unsafe_allow_html=True)