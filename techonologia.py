import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import pdfplumber

# ------------------- Setup -------------------
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"  # Change to "gemini-3.5-flash" or "gemini-3.8-flash" if needed

st.set_page_config(page_title="Notice Simplifier", page_icon="📄", layout="centered")
st.title("Notice Simplifier")
st.caption("Simplify complex notices and government documents into easy language")
st.warning("This is only for understanding. It is not official advice. Always check the original document.")

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
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
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
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text

# ------------------- UI -------------------
language = st.radio("Simplify into:", ["Simple English", "Simple Hindi"], horizontal=True)

st.subheader("Upload or Paste Document")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Upload a file (PDF or TXT)", type=["pdf", "txt"])

with col2:
    document_text = st.text_area("Or paste your notice here", height=150, placeholder="Paste the full notice here...")

final_document = ""

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        final_document = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "text/plain":
        final_document = uploaded_file.read().decode("utf-8")
    
    if final_document:
        st.success(f"File loaded: {uploaded_file.name}")
        with st.expander("Preview extracted text"):
            st.text(final_document[:1200] + ("..." if len(final_document) > 1200 else ""))

elif document_text.strip():
    final_document = document_text.strip()

if st.button("Simplify Document", type="primary", use_container_width=True):
    if not final_document:
        st.error("Please upload a file or paste a document first.")
    else:
        with st.spinner("Simplifying..."):
            try:
                simplified = simplify_document(final_document, language)
                
                st.subheader("Simplified Version")
                with st.container(border=True):
                    st.markdown(simplified)
                
                st.session_state["document"] = final_document
                st.session_state["simplified"] = simplified
            except Exception as e:
                st.error(f"Error while simplifying: {e}")

# Question section
if "document" in st.session_state:
    st.divider()
    st.subheader("Ask a question about this document")
    
    question = st.text_input(
        "Your question",
        placeholder="Example: What is the last date? What do I need to do?"
    )
    
    if st.button("Get Answer", type="secondary") and question:
        with st.spinner("Thinking..."):
            try:
                answer = answer_question(st.session_state["document"], question)
                st.markdown("**Answer:**")
                with st.container(border=True):
                    st.markdown(answer)
            except Exception as e:
                st.error(f"Error while answering: {e}")