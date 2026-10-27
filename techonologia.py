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
    layout="centered"
)

# ------------------- Header -------------------
st.title("Notice Simplifier")
st.caption("Turn official notices and documents into clear, simple language")

st.info("This simplifies text for easier reading. It is not official advice. Always check the original document.")

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

st.write("**Try an example**")
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

st.divider()

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
        "School / Education": "Focus on dates, required documents, and eligibility.",
        "Municipal / Local Body": "Focus on dates, affected areas, and required actions.",
        "Government Scheme": "Focus on eligibility, benefits, documents, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite this document into clear, simple {language}.

{focus}

Rules:
- Use short sentences and everyday words.
- Do not add or invent any information.
- Do not guess.

Format:
**Summary**
(1-2 sentences)

**What to do**
- (actions or none)

**Important dates**
- (dates or none mentioned)

**Other details**
- (remaining points)

Document:
{document}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

def answer_question(document: str, question: str) -> str:
    prompt = f"""Answer using only the document. If not present, reply exactly: "Not mentioned in the document."

Document:
{document}

Question: {question}

Answer:"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

# ------------------- Input -------------------
doc_type = st.selectbox(
    "Document type",
    ["General", "School / Education", "Municipal / Local Body", "Government Scheme"]
)

language = st.radio("Language", ["Simple English", "Simple Hindi"], horizontal=True)

tab1, tab2 = st.tabs(["Upload file", "Paste text"])

final_document = st.session_state.get("example", "")

with tab1:
    uploaded = st.file_uploader("Choose PDF or TXT", type=["pdf", "txt"])
    if uploaded:
        if uploaded.type == "application/pdf":
            final_document = extract_text_from_pdf(uploaded)
        else:
            final_document = uploaded.read().decode("utf-8")
        if final_document:
            st.success(f"Loaded: {uploaded.name}")

with tab2:
    pasted = st.text_area(
        "Paste document",
        value=st.session_state.get("example", ""),
        height=150,
        placeholder="Paste the notice here..."
    )
    if pasted.strip():
        final_document = pasted.strip()

if final_document and len(final_document) > 10000:
    st.warning("Long document — this may take a bit longer.")

if st.button("Simplify", type="primary", use_container_width=True):
    if not final_document.strip():
        st.error("Please upload a file or paste text.")
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
    st.subheader("Simplified")
    st.markdown(st.session_state.result)
    st.download_button(
        "Download as text",
        data=st.session_state.result,
        file_name="simplified.txt",
        mime="text/plain"
    )

# ------------------- Questions -------------------
if "doc" in st.session_state:
    st.divider()
    st.subheader("Ask about this document")
    question = st.text_input("Question", placeholder="What is the deadline? What documents are needed?")
    if st.button("Get answer") and question:
        with st.spinner("Checking..."):
            try:
                answer = answer_question(st.session_state.doc, question)
                st.write(answer)
            except Exception as e:
                st.error(str(e))

# ------------------- History -------------------
if st.session_state.get("history"):
    with st.expander("Recent"):
        for item in st.session_state.history:
            st.write(f"**{item['type']}** — {item['preview']}")
            st.caption(item["result"][:180] + "...")
            st.divider()

st.caption("Always verify important details with the original document.")