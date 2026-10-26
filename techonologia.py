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
    /* Clean modern look */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 780px;
    }
    h1 {
        font-weight: 650;
        letter-spacing: -0.5px;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        height: 3rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        border: 1px solid #e6e6e6;
        background: #fafafa;
    }
    .disclaimer {
        background: #fff8e6;
        border-left: 4px solid #f5a623;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------- Header -------------------
st.markdown("<h1 style='text-align: center; margin-bottom: 0.2rem;'>📄 Notice Simplifier</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; margin-top: 0;'>Turn complex official notices into simple, clear language</p>", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
<strong>Note:</strong> This is only for understanding. It is not official advice. Always verify with the original document.
</div>
""", unsafe_allow_html=True)

st.write("")

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
    prompt = f"""You are an expert at explaining official documents to school students (Class 6–12) in India.

Your only job is to rewrite the given document into very simple, clear, and memorable {language}.

STRICT RULES:
- Use short, easy sentences.
- Use simple everyday words. Avoid difficult or formal language.
- Do NOT add, remove, or change any facts.
- Do NOT invent dates, amounts, rules, or instructions that are not in the document.
- If something is unclear or missing in the original, do not guess.
- Highlight the most important information clearly.
- Structure the output so it is easy to scan and remember.

OUTPUT FORMAT (follow this structure):
**What is this about?**
(One short sentence)

**What do you need to do?**
- Point 1
- Point 2
- Point 3 (only if needed)

**Important Dates / Deadlines**
- (List clearly, or write “No specific date mentioned”)

**Who is this for?**
(One line, or “Not clearly mentioned”)

**Key Points to Remember**
- Point 1
- Point 2

Document to simplify:
{document}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text

def answer_question(document: str, question: str) -> str:
    prompt = f"""You must answer the question using ONLY the information present in the document below.

STRICT RULES:
- Do not use any outside knowledge.
- Do not guess or assume.
- If the answer is not clearly written in the document, reply exactly with: 
  "This information is not mentioned in the document."
- Keep the answer short, clear, and in simple language.
- If the answer has a date, amount, or specific instruction, mention it clearly.

Document:
{document}

Question: {question}

Answer:
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text

# ------------------- Main UI -------------------
language = st.radio(
    "Simplify into",
    ["Simple English", "Simple Hindi"],
    horizontal=True,
    label_visibility="collapsed"
)

st.subheader("Upload or paste your document")

tab1, tab2 = st.tabs(["📤 Upload File", "📝 Paste Text"])

final_document = ""

with tab1:
    uploaded_file = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            final_document = extract_text_from_pdf(uploaded_file)
        else:
            final_document = uploaded_file.read().decode("utf-8")
        if final_document:
            st.success(f"Loaded: {uploaded_file.name}")
            with st.expander("Preview text"):
                st.text(final_document[:1000] + ("..." if len(final_document) > 1000 else ""))

with tab2:
    document_text = st.text_area(
        "Paste notice here",
        height=180,
        placeholder="Paste the full notice or document text here...",
        label_visibility="collapsed"
    )
    if document_text.strip():
        final_document = document_text.strip()

st.write("")

if st.button("Simplify Document", type="primary", use_container_width=True):
    if not final_document:
        st.error("Please upload a file or paste a document first.")
    else:
        with st.spinner("Simplifying your document..."):
            try:
                simplified = simplify_document(final_document, language)
                st.subheader("Simplified Version")
                with st.container(border=True):
                    st.markdown(simplified)
                st.session_state["document"] = final_document
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ------------------- Q&A Section -------------------
if "document" in st.session_state:
    st.divider()
    st.subheader("Ask a question")
    st.caption("Ask anything about the document you just simplified")

    question = st.text_input(
        "Your question",
        placeholder="e.g. What is the last date to apply? What documents do I need?",
        label_visibility="collapsed"
    )

    if st.button("Get Answer", use_container_width=True) and question:
        with st.spinner("Finding the answer..."):
            try:
                answer = answer_question(st.session_state["document"], question)
                st.markdown("**Answer**")
                with st.container(border=True):
                    st.markdown(answer)
            except Exception as e:
                st.error(f"Something went wrong: {e}")