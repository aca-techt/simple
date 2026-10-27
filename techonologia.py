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
st.write("Understand official notices and documents in simple language.")

# ------------------- Examples -------------------
EXAMPLES = {
    "School Scholarship": """Scholarship Notice
Applications are invited from students of Class 9 to 12 for the National Means-cum-Merit Scholarship Scheme.
Last date for online application is 30 November 2026.
Required documents: Aadhaar card, previous year marksheet, income certificate of parents, and bank passbook.
Only applications submitted on the official portal will be accepted. Incomplete forms will be rejected.""",

    "Municipal Water": """Public Notice – Nagar Palika
Due to urgent pipeline repair work, water supply in Ward No. 7 will remain suspended on 18 November 2026 from 9:00 AM to 5:00 PM.
All residents are requested to store sufficient water in advance.
For complaints or assistance, contact the Ward Office between 10:00 AM and 5:00 PM on working days.""",

    "PM-KISAN": """PM-KISAN Scheme Information
Eligible farmer families can check the status of their installment on the official PM-KISAN portal.
The next installment is expected to be credited in December 2026.
Farmers must ensure that their Aadhaar number is linked with their bank account. For help, visit the nearest Common Service Centre or Agriculture Office.""",

    "Exam Notice": """Examination Notice
The half-yearly examination for Classes 9 and 10 will be held from 5 December 2026 to 15 December 2026.
Students must bring their school identity card and admit card.
Reporting time is 8:30 AM. Electronic devices are not allowed inside the examination hall."""
}

with st.expander("Try an example"):
    cols = st.columns(4)
    labels = list(EXAMPLES.keys())
    for i, label in enumerate(labels):
        with cols[i]:
            if st.button(label, use_container_width=True):
                st.session_state.example = EXAMPLES[label]
                st.rerun()

with st.expander("How to use"):
    st.markdown("""
    1. Paste text or upload a PDF/TXT file.  
    2. Choose language and document type.  
    3. Click **Simplify**.  
    4. Read the simplified version or ask questions about it.  
    """)

# ------------------- Functions -------------------
def extract_text_from_pdf(uploaded_file):
    try:
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text.strip()
    except Exception:
        return ""

def simplify_document(document: str, language: str, doc_type: str) -> str:
    focus = {
        "General": "",
        "School / Education": "Pay attention to dates, required documents, eligibility, and deadlines.",
        "Municipal / Local Body": "Pay attention to dates, affected areas, and actions residents must take.",
        "Government Scheme": "Pay attention to eligibility, benefits, required documents, and deadlines."
    }.get(doc_type, "")

    prompt = f"""Rewrite the document into clear, simple {language} that is easy to understand.

{focus}

Rules:
- Use short sentences and everyday words.
- Bold important items such as dates, amounts, deadlines, and required documents.
- Do not add or invent any information.
- Do not guess.

Use this structure:

**Summary**
(1-2 sentences)

**What to do**
- 

**Important dates**
- 

**Required documents / items**
- 

**Other details**
- 

Document:
{document}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

def chat_about_document(document: str, simplified: str, history: list, user_message: str) -> str:
    hist = ""
    for m in history[-5:]:
        role = "User" if m["role"] == "user" else "Assistant"
        hist += f"{role}: {m['content']}\n"

    prompt = f"""Help the user understand the official document below. Use only information from the document and its simplified version.

If the exact answer is not in the document:
- Clearly say it is not mentioned.
- Then give practical next steps (what to check, who to contact if mentioned, related points that are in the document, or what to ask the issuing authority).

Do not invent facts.

Original:
{document}

Simplified:
{simplified}

Conversation:
{hist}

User: {user_message}

Assistant:"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()

# ------------------- Input -------------------
st.subheader("Add your document")

if not st.session_state.get("doc") and not st.session_state.get("example"):
    st.info("Paste a school notice, municipal circular, exam notice, or government scheme to begin.")

doc_type = st.selectbox(
    "Document type",
    ["General", "School / Education", "Municipal / Local Body", "Government Scheme"]
)

language = st.radio("Simplify into", ["Simple English", "Simple Hindi"], horizontal=True)

method = st.radio("Input", ["Paste text", "Upload file"], horizontal=True)

final_document = ""

if method == "Paste text":
    final_document = st.text_area(
        "Paste the notice",
        value=st.session_state.get("example", ""),
        height=170,
        placeholder="Paste the full text here..."
    )
else:
    uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
    if uploaded:
        if uploaded.type == "application/pdf":
            final_document = extract_text_from_pdf(uploaded)
            if not final_document:
                st.error("Could not read text from this PDF. Try pasting the text instead.")
        else:
            final_document = uploaded.read().decode("utf-8", errors="ignore")
        if final_document:
            st.success(f"Loaded {uploaded.name}")

# Stats
if final_document.strip():
    chars = len(final_document.strip())
    words = len(final_document.split())
    st.caption(f"{chars:,} characters · {words:,} words")
    if chars < 40:
        st.warning("Text looks very short.")
    elif chars > 15000:
        st.warning("Long document — simplification may take longer.")

col1, col2 = st.columns([3, 1])
with col1:
    simplify_clicked = st.button("Simplify", type="primary", use_container_width=True, disabled=not final_document.strip())
with col2:
    if st.button("Start over", use_container_width=True):
        for k in ["doc", "result", "chat", "example"]:
            st.session_state.pop(k, None)
        st.rerun()

if simplify_clicked and final_document.strip():
    with st.spinner("Simplifying the document..."):
        try:
            result = simplify_document(final_document, language, doc_type)
            st.session_state.doc = final_document
            st.session_state.result = result
            st.session_state.chat = []
            st.success("Simplified successfully")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# ------------------- Result -------------------
if "result" in st.session_state:
    st.subheader("Result")

    view = st.radio("View", ["Simplified", "Original", "Both"], horizontal=True, label_visibility="collapsed")

    if view == "Simplified":
        st.markdown(st.session_state.result)
    elif view == "Original":
        st.text(st.session_state.doc)
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Original**")
            st.text(st.session_state.doc[:1500] + ("..." if len(st.session_state.doc) > 1500 else ""))
        with c2:
            st.markdown("**Simplified**")
            st.markdown(st.session_state.result)

    st.caption("Based only on the text you provided. Always check the original document.")

    st.download_button(
        "Download simplified text",
        data=st.session_state.result,
        file_name="simplified_notice.txt",
        mime="text/plain"
    )

    # ------------------- Suggested Questions -------------------
    st.write("**Suggested questions**")
    suggestions = [
        "What is the last date or deadline?",
        "What documents or items are required?",
        "What do I need to do?",
        "Who should I contact if I have a problem?"
    ]
    sug_cols = st.columns(2)
    for i, s in enumerate(suggestions):
        with sug_cols[i % 2]:
            if st.button(s, key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_question = s
                st.rerun()

    # ------------------- Chat -------------------
    st.subheader("Ask about this document")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle suggested question
    if "pending_question" in st.session_state:
        q = st.session_state.pop("pending_question")
        st.session_state.chat.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            with st.spinner("Checking the document..."):
                reply = chat_about_document(st.session_state.doc, st.session_state.result, st.session_state.chat, q)
                st.markdown(reply)
                st.session_state.chat.append({"role": "assistant", "content": reply})

    if user_q := st.chat_input("Ask about dates, documents, actions, eligibility..."):
        st.session_state.chat.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)
        with st.chat_message("assistant"):
            with st.spinner("Checking the document..."):
                try:
                    reply = chat_about_document(st.session_state.doc, st.session_state.result, st.session_state.chat, user_q)
                    st.markdown(reply)
                    st.session_state.chat.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(str(e))

    if st.session_state.chat and st.button("Clear chat"):
        st.session_state.chat = []
        st.rerun()

st.divider()
st.caption("Always verify important information with the original document or the issuing authority.")