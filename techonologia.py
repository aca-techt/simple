import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import pdfplumber

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash-lite"

st.set_page_config(page_title="Notice Simplifier", page_icon="📄", layout="centered")

st.title("Notice Simplifier")
st.write("Make official notices and documents easier to understand.")

# ------------------- Examples -------------------
EXAMPLES = {
    "School Scholarship": """Scholarship Notice
Applications are invited from students of Class 9 to 12 for the National Means-cum-Merit Scholarship.
Last date to apply online: 30 November 2026.
Required documents: Aadhaar card, previous year marksheet, income certificate, bank passbook.
Apply only on the official portal. Incomplete applications will be rejected.""",

    "Municipal Notice": """Public Notice
Water supply in Ward 7 will be stopped on 18 November 2026 from 9:00 AM to 5:00 PM for pipeline repair.
Please store water in advance.
Contact the ward office between 10 AM and 5 PM for any issues.""",

    "PM-KISAN": """PM-KISAN Update
Eligible farmers can check installment status on the PM-KISAN portal.
Next installment expected in December 2026.
Make sure Aadhaar and bank account are linked. Visit nearest CSC or agriculture office for help.""",

    "Exam Circular": """Exam Notice
Half-yearly exams for Class 9 and 10 will be held from 5 to 15 December 2026.
Students must carry school ID and admit card.
Reporting time: 8:30 AM. Mobile phones are not allowed in the exam hall."""
}

with st.expander("Load an example"):
    cols = st.columns(2)
    for i, (name, text) in enumerate(EXAMPLES.items()):
        with cols[i % 2]:
            if st.button(name, use_container_width=True, key=f"ex_{i}"):
                st.session_state.example = text
                st.rerun()

with st.expander("How to use this"):
    st.markdown("""
    1. Paste text or upload a PDF/TXT.  
    2. Choose language and type of document.  
    3. Click **Simplify**.  
    4. Read the result or ask questions about it.  
    The tool only uses the text you give it.
    """)

# ------------------- Functions -------------------
def extract_text_from_pdf(file):
    try:
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text.strip()
    except:
        return ""

def simplify_document(doc, language, doc_type):
    focus = {
        "General": "",
        "School / Education": "Focus on deadlines, required documents, and eligibility.",
        "Municipal / Local Body": "Focus on dates, areas affected, and what residents must do.",
        "Government Scheme": "Focus on eligibility, benefits, documents needed, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite the following document into very clear and simple {language}.

{focus}

Rules:
- Short sentences, everyday words.
- Bold dates, deadlines, amounts, and required documents.
- Do not add any information.
- Do not guess.

Structure:
**Summary**
(1-2 short sentences)

**What to do**
- 

**Important dates**
- 

**Documents or items needed**
- 

**Other important points**
- 

Document:
{doc}
"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

def answer_from_document(doc, simplified, history, question):
    hist = "\n".join([f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}" for m in history[-4:]])
    prompt = f"""Answer the user's question using only the document and simplified version below.

If the answer is not in the document:
- Say clearly that it is not mentioned.
- Then give practical next steps (related points from the document, who to contact if mentioned, or what to ask the office).

Do not invent information.

Document:
{doc}

Simplified:
{simplified}

Recent chat:
{hist}

Question: {question}

Answer:"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

# ------------------- Input Section -------------------
st.subheader("1. Add document")

if not any(k in st.session_state for k in ["doc", "example"]):
    st.info("Start by pasting a notice or loading an example above.")

doc_type = st.selectbox("Document type", ["General", "School / Education", "Municipal / Local Body", "Government Scheme"])
language = st.radio("Language", ["Simple English", "Simple Hindi"], horizontal=True)
method = st.radio("How to add", ["Paste", "Upload"], horizontal=True)

text = ""
if method == "Paste":
    text = st.text_area("Paste notice here", value=st.session_state.get("example", ""), height=160)
else:
    f = st.file_uploader("PDF or TXT", type=["pdf", "txt"])
    if f:
        text = extract_text_from_pdf(f) if f.type == "application/pdf" else f.read().decode("utf-8", errors="ignore")
        if not text and f.type == "application/pdf":
            st.error("Could not extract text from this PDF. Please paste the text instead.")
        elif text:
            st.success(f"Loaded {f.name}")

if text.strip():
    st.caption(f"{len(text):,} characters · {len(text.split()):,} words")

c1, c2 = st.columns([4, 1])
with c1:
    do_simplify = st.button("Simplify", type="primary", use_container_width=True, disabled=not text.strip())
with c2:
    if st.button("Reset", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if do_simplify and text.strip():
    with st.spinner("Simplifying..."):
        try:
            simplified = simplify_document(text, language, doc_type)
            st.session_state.doc = text
            st.session_state.result = simplified
            st.session_state.chat = []
            st.success("Done")
        except Exception as e:
            st.error(f"Error: {e}")

# ------------------- Result -------------------
if "result" in st.session_state:
    st.subheader("2. Simplified result")

    mode = st.radio("Show", ["Simplified", "Original", "Side by side"], horizontal=True)
    if mode == "Simplified":
        st.markdown(st.session_state.result)
    elif mode == "Original":
        st.text_area("Original", st.session_state.doc, height=200, disabled=True)
    else:
        left, right = st.columns(2)
        with left:
            st.markdown("**Original**")
            st.text(st.session_state.doc[:1200] + ("..." if len(st.session_state.doc) > 1200 else ""))
        with right:
            st.markdown("**Simplified**")
            st.markdown(st.session_state.result)

    st.caption("Generated only from the text you provided. Always verify with the original document.")

    st.download_button("Download simplified version", st.session_state.result, "simplified.txt", "text/plain")

    # Suggested questions
    st.write("**Quick questions**")
    qs = [
        "What is the deadline?",
        "What documents are required?",
        "What do I need to do?",
        "Is there any contact information?"
    ]
    qcols = st.columns(2)
    for idx, q in enumerate(qs):
        if qcols[idx % 2].button(q, key=f"q{idx}", use_container_width=True):
            st.session_state.pending = q
            st.rerun()

    # Chat
    st.subheader("3. Ask more")
    if "chat" not in st.session_state:
        st.session_state.chat = []

    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if "pending" in st.session_state:
        pq = st.session_state.pop("pending")
        st.session_state.chat.append({"role": "user", "content": pq})
        with st.chat_message("assistant"):
            ans = answer_from_document(st.session_state.doc, st.session_state.result, st.session_state.chat, pq)
            st.write(ans)
            st.session_state.chat.append({"role": "assistant", "content": ans})

    if msg := st.chat_input("Ask anything about this notice..."):
        st.session_state.chat.append({"role": "user", "content": msg})
        with st.chat_message("user"):
            st.write(msg)
        with st.chat_message("assistant"):
            with st.spinner("Looking in the document..."):
                ans = answer_from_document(st.session_state.doc, st.session_state.result, st.session_state.chat, msg)
                st.write(ans)
                st.session_state.chat.append({"role": "assistant", "content": ans})

    if st.session_state.get("chat") and st.button("Clear questions"):
        st.session_state.chat = []
        st.rerun()

st.divider()
st.caption("This tool is for understanding only. It does not replace the original document or official advice.")
st.caption("This tool is created and developed by Advance Computer Academy")