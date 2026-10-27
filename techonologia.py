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

# ------------------- Custom CSS -------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        max-width: 760px;
    }
    h1 { font-weight: 600; letter-spacing: -0.3px; }
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        height: 2.75rem;
    }
    .note {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 0.92rem;
        color: #495057;
        margin-bottom: 1.5rem;
    }
    .footer {
        text-align: center;
        color: #868e96;
        font-size: 0.82rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# ------------------- Header -------------------
st.markdown("<h1 style='text-align: center; margin-bottom: 0.2rem;'>Notice Simplifier</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6c757d; margin-top: 0; margin-bottom: 1.2rem;'>Simplify official notices and documents into clear language</p>", unsafe_allow_html=True)

st.markdown("""
<div class="note">
This tool rewrites documents into simpler language for easier understanding. It is not official advice. Always refer to the original document.
</div>
""", unsafe_allow_html=True)

# ------------------- Example -------------------
EXAMPLE = """Public Notice
All residents are informed that the water supply will be disrupted on 15 November 2026 from 8 AM to 4 PM due to pipeline repair work in Ward 12.
Please store sufficient water in advance. For complaints, contact the Nagar Palika office during working hours.
Issued by: Municipal Corporation"""

if st.button("Load example", use_container_width=True):
    st.session_state["example"] = EXAMPLE

# ------------------- Functions -------------------
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def simplify_document(document: str, language: str) -> str:
    prompt = f"""Rewrite the following document into clear, simple {language}.

Rules:
- Use short sentences and everyday words.
- Keep all facts accurate. Do not add or invent information.
- Do not guess missing details.
- Present the content in a clean, scannable structure.

Structure:
**Summary**
(One or two sentences)

**Action Required**
- (List what needs to be done, if any)

**Important Dates**
- (List dates and deadlines, or state none)

**Other Details**
- (Any other relevant points)

Document:
{document}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

def answer_question(document: str, question: str) -> str:
    prompt = f"""Answer the question using only the information in the document below.

If the answer is not present, respond with: "Not mentioned in the document."

Keep the answer direct and concise.

Document:
{document}

Question: {question}

Answer:"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

# ------------------- Input -------------------
language = st.radio(
    "Output language",
    ["Simple English", "Simple Hindi"],
    horizontal=True
)

st.write("")

tab1, tab2 = st.tabs(["Upload file", "Paste text"])

final_document = st.session_state.get("example", "")

with tab1:
    uploaded_file = st.file_uploader("PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed")
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            final_document = extract_text_from_pdf(uploaded_file)
        else:
            final_document = uploaded_file.read().decode("utf-8")
        if final_document:
            st.success(f"Loaded {uploaded_file.name}")

with tab2:
    pasted = st.text_area(
        "Document text",
        value=st.session_state.get("example", ""),
        height=160,
        placeholder="Paste the notice or document here...",
        label_visibility="collapsed"
    )
    if pasted.strip():
        final_document = pasted.strip()

if final_document and len(final_document) > 10000:
    st.warning("Document is long. Processing may take more time.")

st.write("")

if st.button("Simplify", type="primary", use_container_width=True):
    if not final_document.strip():
        st.error("Please provide a document.")
    else:
        with st.spinner("Processing..."):
            try:
                result = simplify_document(final_document, language)
                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.insert(0, {
                    "preview": final_document[:100] + "...",
                    "result": result,
                    "lang": language
                })
                st.session_state.history = st.session_state.history[:3]
                st.session_state["doc"] = final_document
                st.session_state["result"] = result
            except Exception as e:
                st.error(str(e))

# ------------------- Output -------------------
if "result" in st.session_state:
    st.subheader("Simplified")
    with st.container(border=True):
        st.markdown(st.session_state["result"])

# ------------------- Questions -------------------
if "doc" in st.session_state:
    st.divider()
    st.subheader("Ask about this document")

    q = st.text_input("Question", placeholder="What is the deadline? Who should I contact?", label_visibility="collapsed")

    if st.button("Answer", use_container_width=True) and q:
        with st.spinner("Checking..."):
            try:
                ans = answer_question(st.session_state["doc"], q)
                with st.container(border=True):
                    st.markdown(ans)
            except Exception as e:
                st.error(str(e))

# ------------------- History -------------------
if st.session_state.get("history"):
    with st.expander("Recent"):
        for item in st.session_state.history:
            st.caption(f"{item['lang']} — {item['preview']}")
            st.markdown(item["result"][:250] + "...")
            st.divider()

# ------------------- Footer -------------------
st.markdown("""
<div class="footer">
For easier reading of official documents • Always verify with the original
</div>
""", unsafe_allow_html=True)