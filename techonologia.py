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
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }
    h1 { font-weight: 650; letter-spacing: -0.4px; }
    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        height: 2.8rem;
    }
    .disclaimer {
        background: #fff8e6;
        border-left: 4px solid #f5a623;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 0.94rem;
        margin-bottom: 1.2rem;
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
st.markdown("<h1 style='text-align: center; margin-bottom: 0.15rem;'>📄 Notice Simplifier</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; margin-top: 0; margin-bottom: 1rem;'>Turn complex official notices into simple, clear language</p>", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
<strong>Note:</strong> This is only for understanding. It is not official advice. Always check the original document.
</div>
""", unsafe_allow_html=True)

# ------------------- Example Notice -------------------
EXAMPLE_NOTICE = """Scholarship Application Notice
All students of Class 9 to 12 are hereby informed that applications for the National Means-cum-Merit Scholarship are open.
Last date to apply online is 30 November 2026.
Required documents: Aadhaar card, previous year marksheet, income certificate, and bank passbook.
Apply only on the official portal. Incomplete applications will be rejected.
For more details, contact the school office."""

if st.button("Try with example notice", use_container_width=True):
    st.session_state["example_text"] = EXAMPLE_NOTICE

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

# ------------------- Main Input -------------------
language = st.radio(
    "Simplify into",
    ["Simple English", "Simple Hindi"],
    horizontal=True,
    label_visibility="collapsed"
)

st.subheader("Upload or paste your document")

tab1, tab2 = st.tabs(["📤 Upload File", "📝 Paste Text"])

final_document = st.session_state.get("example_text", "")

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

with tab2:
    pasted = st.text_area(
        "Paste notice here",
        value=st.session_state.get("example_text", ""),
        height=180,
        placeholder="Paste the full notice or document text here...",
        label_visibility="collapsed"
    )
    if pasted.strip():
        final_document = pasted.strip()

# Length warning
if final_document and len(final_document) > 8000:
    st.warning("This document is quite long. Simplification may take longer or cost more tokens.")

st.write("")

if st.button("Simplify Document", type="primary", use_container_width=True):
    if not final_document.strip():
        st.error("Please upload a file or paste a document first.")
    else:
        with st.spinner("Simplifying... (usually 5–12 seconds)"):
            try:
                simplified = simplify_document(final_document, language)
                
                # Save to history
                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.insert(0, {
                    "original_preview": final_document[:120] + "...",
                    "simplified": simplified,
                    "language": language
                })
                st.session_state.history = st.session_state.history[:3]
                
                st.session_state["document"] = final_document
                st.session_state["last_simplified"] = simplified
                st.success("Simplified successfully")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ------------------- Result -------------------
if "last_simplified" in st.session_state:
    st.subheader("Simplified Version")
    with st.container(border=True):
        st.markdown(st.session_state["last_simplified"])
    
    # Copy button
    st.code(st.session_state["last_simplified"], language=None)
    st.caption("Select the text above and copy it, or use your browser’s copy function.")

# ------------------- Q&A -------------------
if "document" in st.session_state:
    st.divider()
    st.subheader("Ask a question")
    st.caption("Ask anything about the document")

    question = st.text_input(
        "Your question",
        placeholder="e.g. What is the last date? What documents are needed?",
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

# ------------------- History -------------------
if "history" in st.session_state and st.session_state.history:
    with st.expander("Recent simplifications"):
        for i, item in enumerate(st.session_state.history):
            st.markdown(f"**{i+1}. {item['language']}** — {item['original_preview']}")
            st.markdown(item["simplified"][:300] + "...")
            st.divider()

# ------------------- How it works -------------------
with st.expander("How it works"):
    st.markdown("""
    1. Upload a PDF/TXT or paste the notice text.  
    2. Choose Simple English or Simple Hindi.  
    3. Click **Simplify Document**.  
    4. Ask questions about the same document if needed.  

    The AI only uses the text you provide. It does not search the internet.
    """)

# ------------------- Footer -------------------
st.markdown("""
<div class="footer">
Built for school students • Not legal advice • Always verify with the original document
</div>
""", unsafe_allow_html=True)