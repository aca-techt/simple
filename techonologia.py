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

# ------------------- Simple clean CSS -------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 700px;
    }
    h1 {
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
    }
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# ------------------- Header -------------------
st.title("Notice Simplifier")
st.caption("Rewrite official notices and documents into clear, simple language")

st.info("This tool simplifies text for easier reading. It is not official advice. Always check the original document.")

# ------------------- Examples -------------------
EXAMPLES = {
    "School": """Scholarship Notice
Applications are invited from students of Class 9 to 12 for the National Means-cum-Merit Scholarship.
Last date to apply: 30 November 2026.
Required documents: Aadhaar card, previous year marksheet, income certificate, and bank passbook.
Apply only through the official portal. Incomplete applications will not be accepted.""",

    "Municipal": """Public Notice
Water supply in Ward 7 will remain suspended on 18 November 2026 from 9:00 AM to 5:00 PM due to pipeline repair work.
Residents are advised to store sufficient water in advance.
For any issues, contact the ward office between 10:00 AM and 5:00 PM.""",

    "Scheme": """PM-KISAN Scheme
Eligible farmers may check the status of their installment on the official PM-KISAN portal.
The next installment is expected to be released in December 2026.
Please ensure that your Aadhaar number and bank account are correctly linked."""
}

st.write("**Try an example**")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("School notice", use_container_width=True):
        st.session_state.example = EXAMPLES["School"]
with c2:
    if st.button("Municipal notice", use_container_width=True):
        st.session_state.example = EXAMPLES["Municipal"]
with c3:
    if st.button("Farmer scheme", use_container_width=True):
        st.session_state.example = EXAMPLES["Scheme"]

st.divider()

# ------------------- Functions -------------------
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def simplify_document(document: str, language: str, doc_type: str) -> str:
    focus = {
        "General": "",
        "School / Education": "Pay special attention to dates, required documents, and eligibility.",
        "Municipal / Local Body": "Pay special attention to dates, affected areas, and actions residents must take.",
        "Government Scheme": "Pay special attention to eligibility, benefits, required documents, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite the following document into clear and simple {language}.

{focus}

Instructions:
- Use short sentences and common words.
- Do not add any information that is not in the original document.
- Do not guess or invent details.
- Organize the output clearly.

Format:
**Summary**
(One or two sentences)

**What you need to do**
- (List actions, if any)

**Important dates**
- (List dates, or write "None mentioned")

**Other information**
- (Any remaining useful points)

Document:
{document}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

def answer_question(document: str, question: str) -> str:
    prompt = f"""Answer the question using only the information in the document below.
If the answer is not in the document, reply exactly: "Not mentioned in the document."

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

language = st.radio("Output language", ["Simple English", "Simple Hindi"], horizontal=True)

tab1, tab2 = st.tabs(["Upload file", "Paste text"])

final_document = st.session_state.get("example", "")

with tab1:
    uploaded_file = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            final_document = extract_text_from_pdf(uploaded_file)
        else:
            final_document = uploaded_file.read().decode("utf-8")
        if final_document:
            st.success(f"Loaded: {uploaded_file.name}")

with tab2:
    pasted_text = st.text_area(
        "Paste the document text",
        value=st.session_state.get("example", ""),
        height=160,
        placeholder="Paste the full notice or document here..."
    )
    if pasted_text.strip():
        final_document = pasted_text.strip()

if final_document and len(final_document) > 10000:
    st.warning("This document is long. Simplification may take a little longer.")

if st.button("Simplify", type="primary", use_container_width=True):
    if not final_document.strip():
        st.error("Please upload a file or paste some text.")
    else:
        with st.spinner("Simplifying..."):
            try:
                result = simplify_document(final_document, language, doc_type)
                st.session_state.doc = final_document
                st.session_state.result = result

                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.insert(0, {
                    "preview": final_document[:100] + "...",
                    "result": result,
                    "type": doc_type
                })
                st.session_state.history = st.session_state.history[:3]
            except Exception as e:
                st.error(f"Error: {e}")

# ------------------- Result -------------------
if "result" in st.session_state:
    st.subheader("Simplified version")
    st.markdown(st.session_state.result)

    st.download_button(
        label="Download as text file",
        data=st.session_state.result,
        file_name="simplified_notice.txt",
        mime="text/plain"
    )

# ------------------- Questions -------------------
if "doc" in st.session_state:
    st.divider()
    st.subheader("Ask a question about this document")
    question = st.text_input("Your question", placeholder="Example: What is the last date? What documents are required?")

    if st.button("Get answer") and question:
        with st.spinner("Looking in the document..."):
            try:
                answer = answer_question(st.session_state.doc, question)
                st.markdown("**Answer**")
                st.write(answer)
            except Exception as e:
                st.error(f"Error: {e}")

# ------------------- History -------------------
if st.session_state.get("history"):
    with st.expander("Recent documents"):
        for item in st.session_state.history:
            st.write(f"**{item['type']}** — {item['preview']}")
            st.caption(item["result"][:200] + "...")
            st.divider()

# ------------------- Footer -------------------
st.markdown('<div class="footer">Always check the original document for accuracy</div>', unsafe_allow_html=True)