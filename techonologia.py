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
st.write("Turn an official notice into simple language, then see what people often miss and what the notice left out.")

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

def extract_text_from_pdf(file):
    try:
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text.strip()
    except Exception:
        return ""

def analyze_document(doc, language, doc_type):
    focus = {
        "General": "",
        "School / Education": "Think about students and parents.",
        "Municipal / Local Body": "Think about residents.",
        "Government Scheme": "Think about people applying for a scheme."
    }.get(doc_type, "")

    prompt = f"""Read the official document below. Reply in {language}. {focus}

Use ONLY facts from the document. Do not invent dates, rules, phone numbers, or offices.

Return exactly these three sections:

## Simplified
Rewrite in short, simple sentences.
Bold dates, deadlines, and required documents.
Include:
- Summary (1-2 sentences)
- What to do
- Important dates
- Documents or items needed
- Other important points

## What can go wrong
List 3 to 5 specific mistakes a person could make with THIS notice.
Each point must be based on something actually written in the document.
Example style: missing a date that is written, forgetting a listed document, applying the wrong way.
If you cannot find real risks, write: "No clear risk is stated in this notice."

## Missing information
List important details a reader would normally need that are NOT written in this notice.
Examples: no contact number, no office address, no fee amount, no exact link, no eligibility rule.
Only list things that are truly absent.
If nothing important is missing, write: "No major gap is obvious from this text."

Document:
{doc}
"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

def split_sections(text):
    parts = {"simplified": "", "wrong": "", "missing": ""}
    current = None
    buf = []
    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith("## simplified"):
            if current:
                parts[current] = "\n".join(buf).strip()
            current = "simplified"
            buf = []
        elif low.startswith("## what can go wrong"):
            if current:
                parts[current] = "\n".join(buf).strip()
            current = "wrong"
            buf = []
        elif low.startswith("## missing information"):
            if current:
                parts[current] = "\n".join(buf).strip()
            current = "missing"
            buf = []
        else:
            buf.append(line)
    if current:
        parts[current] = "\n".join(buf).strip()
    return parts

def answer_from_document(doc, analysis, history, question):
    hist = "\n".join(
        [f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}" for m in history[-4:]]
    )
    prompt = f"""Answer using only the document and the analysis below.
If the answer is not in the document, say it is not mentioned, then give a practical next step.
Do not invent facts.

Document:
{doc}

Analysis:
{analysis}

Recent chat:
{hist}

Question: {question}

Answer:"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

st.subheader("1. Add document")

doc_type = st.selectbox(
    "Document type",
    ["General", "School / Education", "Municipal / Local Body", "Government Scheme"]
)
language = st.radio("Language", ["Simple English", "Simple Hindi"], horizontal=True)
method = st.radio("How to add", ["Paste", "Upload"], horizontal=True)

text = ""
if method == "Paste":
    text = st.text_area(
        "Paste notice here",
        value=st.session_state.get("example", ""),
        height=160
    )
else:
    f = st.file_uploader("PDF or TXT", type=["pdf", "txt"])
    if f:
        text = extract_text_from_pdf(f) if f.type == "application/pdf" else f.read().decode("utf-8", errors="ignore")
        if f.type == "application/pdf" and not text:
            st.error("Could not read this PDF. Paste the text instead.")
        elif text:
            st.success(f"Loaded {f.name}")

if text.strip():
    st.caption(f"{len(text):,} characters · {len(text.split()):,} words")

c1, c2 = st.columns([4, 1])
with c1:
    do_it = st.button("Analyze", type="primary", use_container_width=True, disabled=not text.strip())
with c2:
    if st.button("Reset", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if do_it and text.strip():
    with st.spinner("Reading the notice..."):
        try:
            raw = analyze_document(text, language, doc_type)
            parts = split_sections(raw)
            st.session_state.doc = text
            st.session_state.raw = raw
            st.session_state.parts = parts
            st.session_state.chat = []
        except Exception as e:
            st.error(f"Error: {e}")

if "parts" in st.session_state:
    parts = st.session_state.parts

    st.subheader("2. Simplified")
    if parts["simplified"]:
        st.markdown(parts["simplified"])
    else:
        st.markdown(st.session_state.raw)

    st.subheader("3. What can go wrong")
    st.warning(parts["wrong"] or "No clear risk is stated in this notice.")

    st.subheader("4. Missing information")
    st.info(parts["missing"] or "No major gap is obvious from this text.")

    st.caption("These points come only from the text you provided. Always check the original notice.")

    download_text = (
        "SIMPLIFIED\n" + (parts["simplified"] or st.session_state.raw)
        + "\n\nWHAT CAN GO WRONG\n" + (parts["wrong"] or "")
        + "\n\nMISSING INFORMATION\n" + (parts["missing"] or "")
    )
    st.download_button(
        "Download full analysis",
        data=download_text,
        file_name="notice_analysis.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.subheader("5. Ask about this notice")
    if "chat" not in st.session_state:
        st.session_state.chat = []

    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if msg := st.chat_input("Ask about dates, documents, or what to do..."):
        st.session_state.chat.append({"role": "user", "content": msg})
        with st.chat_message("user"):
            st.write(msg)
        with st.chat_message("assistant"):
            with st.spinner("Checking the notice..."):
                ans = answer_from_document(
                    st.session_state.doc,
                    st.session_state.raw,
                    st.session_state.chat,
                    msg
                )
                st.write(ans)
                st.session_state.chat.append({"role": "assistant", "content": ans})

st.divider()
st.caption("For understanding only. Not official advice.")