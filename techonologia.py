import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import pdfplumber

# ------------------- Setup -------------------
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Recommended models (pick one):
# MODEL = "gemini-3.5-flash"          # Better quality
MODEL = "gemini-3.5-flash-lite"       

st.set_page_config(page_title="Notice Simplifier", page_icon="📄")
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
    prompt = f"""
You are helping school students (class 6-12) understand official documents.

Task: Rewrite the following document in very simple, clear, and memorable {language}.

Rules:
- Use short sentences
- Use easy words
- Highlight important things like dates, deadlines, and what the person must do
- Keep the meaning accurate
- Do not add any information that is not in the document
- Make it easy to remember

Document:
{document}
"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text

def answer_question(document: str, question: str) -> str:
    prompt = f"""
Answer the user's question based ONLY on the document below.
If the answer is not in the document, say "This information is not mentioned in the document."

Document:
{document}

Question: {question}

Answer in simple language:
"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text

# ------------------- UI -------------------
language = st.radio("Simplify into:", ["Simple English", "Simple Hindi"], horizontal=True)

st.subheader("Upload or Paste Document")

uploaded_file = st.file_uploader("Upload a file (PDF or TXT)", type=["pdf", "txt"])
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
            st.text(final_document[:1000] + ("..." if len(final_document) > 1000 else ""))

elif document_text.strip():
    final_document = document_text.strip()

if st.button("Simplify Document", type="primary"):
    if not final_document:
        st.error("Please upload a file or paste a document first.")
    else:
        with st.spinner("Simplifying..."):
            try:
                simplified = simplify_document(final_document, language)
                st.subheader("Simplified Version")
                st.write(simplified)

                st.session_state["document"] = final_document
                st.session_state["simplified"] = simplified
            except Exception as e:
                st.error(f"Error while simplifying: {e}")

if "document" in st.session_state:
    st.divider()
    st.subheader("Ask a question about this document")
    question = st.text_input("Your question", placeholder="Example: What is the last date? What do I need to do?")

    if st.button("Get Answer") and question:
        with st.spinner("Thinking..."):
            try:
                answer = answer_question(st.session_state["document"], question)
                st.write(answer)
            except Exception as e:
                st.error(f"Error while answering: {e}")