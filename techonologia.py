import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import pdfplumber

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash-lite"

st.set_page_config(page_title="Saral-it", page_icon="📄", layout="centered")

st.title("Saral-it")
st.write("Simplify notices or analyse what is missing.")

# Mode toggle
mode = st.radio(
    "Choose",
    ["Saral-it", "Analyse"],
    horizontal=True,
    label_visibility="collapsed"
)

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
}

with st.expander("Load an example"):
    cols = st.columns(3)
    for i, (name, text) in enumerate(EXAMPLES.items()):
        with cols[i]:
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

def simplify_document(doc, language):
    prompt = f"""Rewrite the following document into clear, simple {language}.

Rules:
- Short sentences, everyday words.
- Bold dates, deadlines, and required documents.
- Do not add or invent any information.
- Do not guess.

Structure:
**Summary**
(1-2 sentences)

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

def analyse_document(doc, language):
    prompt = f"""Read the official document below. Reply in {language}.

Use ONLY facts from the document. Do not invent dates, rules, or contact details.

Return exactly these two sections:

## What can go wrong
List 3 to 5 specific mistakes a person could make with THIS notice.
Each point must be based on something actually written in the document.
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

def split_analyse(text):
    parts = {"wrong": "", "missing": ""}
    current = None
    buf = []
    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith("## what can go wrong"):
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

# Input
st.subheader("Add document")

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
    st.caption(f"{len(text):,} characters")

col1, col2 = st.columns(2)
with col1:
    saral = st.button("Saral-it", type="primary", use_container_width=True, disabled=not text.strip())
with col2:
    analyse = st.button("Analyse", use_container_width=True, disabled=not text.strip())

if st.button("Reset"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# Saral-it
if saral and text.strip():
    with st.spinner("Simplifying..."):
        try:
            result = simplify_document(text, language)
            st.session_state.mode_result = "saral"
            st.session_state.simplified = result
            st.session_state.doc = text
        except Exception as e:
            st.error(str(e))

# Analyse
if analyse and text.strip():
    with st.spinner("Analysing..."):
        try:
            raw = analyse_document(text, language)
            parts = split_analyse(raw)
            st.session_state.mode_result = "analyse"
            st.session_state.analyse_parts = parts
            st.session_state.doc = text
        except Exception as e:
            st.error(str(e))

# Show results based on mode
if st.session_state.get("mode_result") == "saral" and "simplified" in st.session_state:
    st.subheader("Simplified")
    st.markdown(st.session_state.simplified)
    st.caption("Based only on the text you provided. Always check the original document.")
    st.download_button(
        "Download simplified text",
        data=st.session_state.simplified,
        file_name="simplified.txt",
        mime="text/plain"
    )

if st.session_state.get("mode_result") == "analyse" and "analyse_parts" in st.session_state:
    parts = st.session_state.analyse_parts
    st.subheader("What can go wrong")
    st.warning(parts.get("wrong") or "No clear risk is stated in this notice.")

    st.subheader("Missing information")
    st.info(parts.get("missing") or "No major gap is obvious from this text.")

    st.caption("These points come only from the text you provided.")

    download_text = (
        "WHAT CAN GO WRONG\n" + (parts.get("wrong") or "")
        + "\n\nMISSING INFORMATION\n" + (parts.get("missing") or "")
    )
    st.download_button(
        "Download analysis",
        data=download_text,
        file_name="analysis.txt",
        mime="text/plain"
    )

st.divider()
st.caption("For understanding only. Not official advice.")
st.caption("This web app is developed by Advance Computer Academy")