import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import pdfplumber

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash-lite"

st.set_page_config(page_title="Saral-it", page_icon="📄", layout="centered")

# Branding CSS
st.markdown("""
<style>
    .saral-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .saral-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #1565C0;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .saral-tagline {
        color: #1976D2;
        font-size: 0.85rem;
        letter-spacing: 1.5px;
        margin-top: 0.3rem;
        font-weight: 500;
    }
    .stButton > button[kind="primary"] {
        background-color: #1565C0;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #0D47A1;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="saral-header">
    <div class="saral-title">सरल It</div>
    <div class="saral-tagline">SOLUTIONS. SIMPLE. SMART.</div>
</div>
""", unsafe_allow_html=True)

st.write("")

# Language toggle
lang_choice = st.radio(
    "Language / भाषा",
    ["English", "हिंदी"],
    horizontal=True
)
is_hindi = lang_choice == "हिंदी"

# Labels based on language
labels = {
    "subtitle": "Simplify notices or analyse what is missing." if not is_hindi else "नोटिस को सरल बनाएं या जानें क्या जानकारी गायब है।",
    "mode_saral": "Saral-it" if not is_hindi else "सरल करें",
    "mode_analyse": "Analyse" if not is_hindi else "विश्लेषण",
    "add_doc": "Add document" if not is_hindi else "दस्तावेज़ जोड़ें",
    "paste": "Paste" if not is_hindi else "पेस्ट करें",
    "upload": "Upload" if not is_hindi else "अपलोड करें",
    "paste_here": "Paste notice here" if not is_hindi else "नोटिस यहाँ पेस्ट करें",
    "simplify_btn": "Saral-it" if not is_hindi else "सरल करें",
    "analyse_btn": "Analyse" if not is_hindi else "विश्लेषण करें",
    "reset": "Reset" if not is_hindi else "रीसेट",
    "simplified": "Simplified" if not is_hindi else "सरल संस्करण",
    "what_wrong": "What can go wrong" if not is_hindi else "क्या गलत हो सकता है",
    "missing": "Missing information" if not is_hindi else "गायब जानकारी",
    "download": "Download" if not is_hindi else "डाउनलोड",
    "disclaimer": "Based only on the text you provided. Always check the original document." if not is_hindi else "केवल आपके दिए गए पाठ पर आधारित। हमेशा मूल दस्तावेज़ जांचें।",
    "output_lang": "Simple Hindi" if is_hindi else "Simple English"
}

st.caption(labels["subtitle"])

# Mode
mode = st.radio(
    "Choose",
    [labels["mode_saral"], labels["mode_analyse"]],
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

with st.expander("Load an example" if not is_hindi else "उदाहरण लोड करें"):
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
        if "what can go wrong" in low or "गलत हो सकता" in low:
            if current:
                parts[current] = "\n".join(buf).strip()
            current = "wrong"
            buf = []
        elif "missing information" in low or "गायब जानकारी" in low:
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
st.subheader(labels["add_doc"])

method = st.radio(
    "How to add",
    [labels["paste"], labels["upload"]],
    horizontal=True,
    label_visibility="collapsed"
)

text = ""
if method == labels["paste"]:
    text = st.text_area(
        labels["paste_here"],
        value=st.session_state.get("example", ""),
        height=160,
        label_visibility="collapsed"
    )
else:
    f = st.file_uploader("PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed")
    if f:
        text = extract_text_from_pdf(f) if f.type == "application/pdf" else f.read().decode("utf-8", errors="ignore")
        if f.type == "application/pdf" and not text:
            st.error("Could not read this PDF. Paste the text instead." if not is_hindi else "इस PDF से टेक्स्ट नहीं पढ़ा जा सका। टेक्स्ट पेस्ट करें।")
        elif text:
            st.success(f"Loaded {f.name}" if not is_hindi else f"लोड हो गया: {f.name}")

if text.strip():
    st.caption(f"{len(text):,} characters" if not is_hindi else f"{len(text):,} अक्षर")

col1, col2 = st.columns(2)
with col1:
    saral = st.button(labels["simplify_btn"], type="primary", use_container_width=True, disabled=not text.strip())
with col2:
    analyse = st.button(labels["analyse_btn"], use_container_width=True, disabled=not text.strip())

if st.button(labels["reset"]):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

output_lang = labels["output_lang"]

if saral and text.strip():
    with st.spinner("Simplifying..." if not is_hindi else "सरल कर रहे हैं..."):
        try:
            result = simplify_document(text, output_lang)
            st.session_state.mode_result = "saral"
            st.session_state.simplified = result
            st.session_state.doc = text
        except Exception as e:
            st.error(str(e))

if analyse and text.strip():
    with st.spinner("Analysing..." if not is_hindi else "विश्लेषण कर रहे हैं..."):
        try:
            raw = analyse_document(text, output_lang)
            parts = split_analyse(raw)
            st.session_state.mode_result = "analyse"
            st.session_state.analyse_parts = parts
            st.session_state.doc = text
        except Exception as e:
            st.error(str(e))

# Results
if st.session_state.get("mode_result") == "saral" and "simplified" in st.session_state:
    st.subheader(labels["simplified"])
    st.markdown(st.session_state.simplified)
    st.caption(labels["disclaimer"])
    st.download_button(
        labels["download"],
        data=st.session_state.simplified,
        file_name="simplified.txt",
        mime="text/plain"
    )

if st.session_state.get("mode_result") == "analyse" and "analyse_parts" in st.session_state:
    parts = st.session_state.analyse_parts
    st.subheader(labels["what_wrong"])
    st.warning(parts.get("wrong") or ("No clear risk is stated in this notice." if not is_hindi else "इस नोटिस में कोई स्पष्ट जोखिम नहीं बताया गया।"))

    st.subheader(labels["missing"])
    st.info(parts.get("missing") or ("No major gap is obvious from this text." if not is_hindi else "इस पाठ से कोई बड़ी कमी स्पष्ट नहीं है।"))

    st.caption(labels["disclaimer"])

    download_text = (
        f"{labels['what_wrong']}\n" + (parts.get("wrong") or "")
        + f"\n\n{labels['missing']}\n" + (parts.get("missing") or "")
    )
    st.download_button(
        labels["download"],
        data=download_text,
        file_name="analysis.txt",
        mime="text/plain"
    )

st.divider()
st.caption("For understanding only. Not official advice." if not is_hindi else "केवल समझने के लिए। आधिकारिक सलाह नहीं।")