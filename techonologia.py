import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import pdfplumber

# ------------------- Setup -------------------
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"

st.set_page_config(page_title="Notice Simplifier", page_icon="📄", layout="centered")

st.title("Notice Simplifier")
st.write("Paste or upload an official notice. Get a clear, simple version.")

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

with st.expander("Not sure what to try? Load an example"):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("School notice"):
            st.session_state.example = EXAMPLES["School"]
            st.rerun()
    with c2:
        if st.button("Municipal notice"):
            st.session_state.example = EXAMPLES["Municipal"]
            st.rerun()
    with c3:
        if st.button("Farmer scheme"):
            st.session_state.example = EXAMPLES["Scheme"]
            st.rerun()

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
        "School / Education": "Highlight dates, required documents, and eligibility.",
        "Municipal / Local Body": "Highlight dates, affected areas, and what people must do.",
        "Government Scheme": "Highlight eligibility, benefits, documents needed, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite into clear, simple {language}.

{focus}

Use short sentences. Do not add information. Do not guess.

**Summary**
(1-2 sentences)

**What to do**
-

**Important dates**
-

**Other details**
-

Document:
{document}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

def answer_question(document: str, question: str) -> str:
    prompt = f"""Answer only from the document. If missing, say exactly: "Not mentioned in the document."

Document:
{document}

Question: {question}

Answer:"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

# ------------------- Main Input -------------------
st.subheader("1. Add your document")

doc_type = st.selectbox(
    "What kind of document is this?",
    ["General", "School / Education", "Municipal / Local Body", "Government Scheme"],
    help="This helps the simplification focus on the right details."
)

language = st.radio("Simplify into", ["Simple English", "Simple Hindi"], horizontal=True)

input_method = st.radio("How do you want to add it?", ["Paste text", "Upload file"], horizontal=True)

final_document = ""

if input_method == "Paste text":
    final_document = st.text_area(
        "Paste the notice here",
        value=st.session_state.get("example", ""),
        height=180,
        placeholder="Paste the full text of the notice or document..."
    )
else:
    uploaded = st.file_uploader("Upload PDF or TXT file", type=["pdf", "txt"])
    if uploaded:
        if uploaded.type == "application/pdf":
            final_document = extract_text_from_pdf(uploaded)
        else:
            final_document = uploaded.read().decode("utf-8")
        if final_document:
            st.success(f"Loaded {uploaded.name} ({len(final_document)} characters)")
            with st.expander("Preview extracted text"):
                st.text(final_document[:800] + ("..." if len(final_document) > 800 else ""))

# Length feedback
if final_document:
    char_count = len(final_document.strip())
    if char_count < 50:
        st.warning("This looks very short. Make sure you pasted the full notice.")
    elif char_count > 12000:
        st.warning("This is a long document. Simplification may take longer.")

# ------------------- Action -------------------
st.subheader("2. Simplify")

if st.button("Simplify now", type="primary", use_container_width=True, disabled=not final_document.strip()):
    with st.spinner("Reading and simplifying..."):
        try:
            result = simplify_document(final_document, language, doc_type)
            st.session_state.doc = final_document
            st.session_state.result = result
            st.session_state.language_used = language
            if "history" not in st.session_state:
                st.session_state.history = []
            st.session_state.history.insert(0, {
                "preview": final_document[:80] + "...",
                "result": result,
                "type": doc_type
            })
            st.session_state.history = st.session_state.history[:3]
            st.success("Done")
        except Exception as e:
            st.error(f"Could not simplify: {e}")

# ------------------- Result -------------------
if "result" in st.session_state:
    st.subheader("Simplified version")
    st.markdown(st.session_state.result)

    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "Download",
            data=st.session_state.result,
            file_name="simplified.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_b:
        if st.button("Simplify another", use_container_width=True):
            for key in ["result", "doc", "example"]:
                st.session_state.pop(key, None)
            st.rerun()

# ------------------- Questions -------------------
if "doc" in st.session_state:
    st.divider()
    st.subheader("3. Ask a question (optional)")
    st.caption("Answers come only from the document you just simplified.")

    question = st.text_input("Your question", placeholder="What is the last date? What documents do I need?")

    if st.button("Get answer", disabled=not question) and question:
        with st.spinner("Checking the document..."):
            try:
                answer = answer_question(st.session_state.doc, question)
                st.write(answer)
            except Exception as e:
                st.error(str(e))

# ------------------- History -------------------
if st.session_state.get("history"):
    with st.expander("Previous simplifications"):
        for i, item in enumerate(st.session_state.history):
            st.write(f"**{item['type']}** — {item['preview']}")
            if st.button(f"Show again", key=f"hist_{i}"):
                st.session_state.result = item["result"]
                st.rerun()
            st.divider()

st.caption("Always double-check important details against the original document.")