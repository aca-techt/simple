import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
import pdfplumber

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash-lite"

st.set_page_config(page_title="Saral IT", page_icon="📄", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@600;700;800&display=swap');

.stApp { background: #F8FAFC; font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; max-width: 720px; }

.header-bar {
    background: #111827;
    color: #F8FAFC;
    padding: 1.4rem 1.6rem 1.2rem 1.6rem;
    border-radius: 16px;
    margin-bottom: 1.4rem;
}
.header-title {
    font-family: 'Manrope', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.6px;
    color: #F8FAFC;
}
.header-title span { color: #C8F169; }
.header-tag {
    font-size: 0.78rem;
    letter-spacing: 1.8px;
    margin-top: 4px;
    color: #94A3B8;
    font-weight: 500;
    text-transform: uppercase;
}

h1, h2, h3, .stSubheader {
    font-family: 'Manrope', sans-serif !important;
    color: #172033 !important;
    font-weight: 700 !important;
}
.stMarkdown, p, label, .stCaption { color: #172033; }
.stCaption { color: #64748B !important; font-size: 0.85rem; }

.stButton > button {
    border-radius: 9px;
    height: 46px;
    font-weight: 600;
    font-size: 0.95rem;
    border: none;
    font-family: 'Inter', sans-serif;
}
.stButton > button[kind="primary"] {
    background: #315EFB;
    color: #FFFFFF;
}
.stButton > button[kind="primary"]:hover {
    background: #2449D8;
}
.stButton > button:not([kind="primary"]) {
    background: #FFFFFF;
    color: #172033;
    border: 1px solid #E5EAF2;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #315EFB;
    color: #315EFB;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E5EAF2;
    border-radius: 14px;
    box-shadow: 0 1px 3px rgba(17, 24, 39, 0.04);
}

.stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background: #FFFFFF !important;
    border: 1px solid #E5EAF2 !important;
    border-radius: 8px !important;
    color: #172033 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #315EFB !important;
    box-shadow: 0 0 0 3px rgba(49, 94, 251, 0.12);
}

.stRadio > div { gap: 0.6rem; }
.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-bar">
    <div class="header-title">Saral <span>IT</span></div>
    <div class="header-tag">Legal document clarity · Simple · Precise</div>
</div>
""", unsafe_allow_html=True)

lang_choice = st.radio("Language / भाषा", ["English", "हिंदी"], horizontal=True)
is_hindi = lang_choice == "हिंदी"

labels = {
    "subtitle": "Turn official notices into clear language, or analyse what is missing." if not is_hindi else "आधिकारिक नोटिस को सरल भाषा में बदलें, या जानें क्या जानकारी गायब है।",
    "mode_saral": "Saral-it" if not is_hindi else "सरल करें",
    "mode_analyse": "Analyse" if not is_hindi else "विश्लेषण",
    "add_doc": "Document" if not is_hindi else "दस्तावेज़",
    "paste": "Paste" if not is_hindi else "पेस्ट",
    "upload": "Upload" if not is_hindi else "अपलोड",
    "paste_here": "Paste the notice here…" if not is_hindi else "नोटिस यहाँ पेस्ट करें…",
    "simplify_btn": "Saral-it" if not is_hindi else "सरल करें",
    "analyse_btn": "Analyse" if not is_hindi else "विश्लेषण",
    "reset": "Start over" if not is_hindi else "फिर से शुरू",
    "simplified": "Simplified" if not is_hindi else "सरल संस्करण",
    "what_wrong": "What can go wrong" if not is_hindi else "क्या गलत हो सकता है",
    "missing": "Missing information" if not is_hindi else "गायब जानकारी",
    "download": "Download" if not is_hindi else "डाउनलोड",
    "disclaimer": "Based only on the text you provided. Always verify with the original document." if not is_hindi else "केवल आपके दिए पाठ पर आधारित। हमेशा मूल दस्तावेज़ जांचें।",
    "output_lang": "Simple Hindi" if is_hindi else "Simple English",
    "ask": "Ask about this notice" if not is_hindi else "इस नोटिस के बारे में पूछें",
    "ask_placeholder": "Ask about dates, documents, or what to do..." if not is_hindi else "तारीख, दस्तावेज़ या क्या करना है पूछें..."
}

st.caption(labels["subtitle"])

mode = st.radio(
    "Mode",
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

with st.expander("Try an example" if not is_hindi else "उदाहरण देखें"):
    c1, c2, c3 = st.columns(3)
    for i, (name, txt) in enumerate(EXAMPLES.items()):
        with [c1, c2, c3][i]:
            if st.button(name.split()[0], use_container_width=True, key=f"ex{i}"):
                st.session_state.example = txt
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
    prompt = f"""Rewrite into clear, simple {language}.
Short sentences. Bold dates and required documents. Do not invent information.

**Summary**
**What to do**
**Important dates**
**Documents needed**
**Other points**

Document:
{doc}"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

def analyse_document(doc, language):
    prompt = f"""Reply in {language}. Use only the document. Do not invent facts.

## What can go wrong
3-5 specific mistakes based on this notice. If none: "No clear risk is stated."

## Missing information
Important details that are absent. If none: "No major gap is obvious."

Document:
{doc}"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

def split_analyse(text):
    parts = {"wrong": "", "missing": ""}
    current = None
    buf = []
    for line in text.splitlines():
        low = line.strip().lower()
        if "what can go wrong" in low or "गलत हो सकता" in low:
            if current: parts[current] = "\n".join(buf).strip()
            current, buf = "wrong", []
        elif "missing information" in low or "गायब जानकारी" in low:
            if current: parts[current] = "\n".join(buf).strip()
            current, buf = "missing", []
        else:
            buf.append(line)
    if current:
        parts[current] = "\n".join(buf).strip()
    return parts

def answer_from_document(doc, context, history, question):
    hist = "\n".join(
        [f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}" for m in history[-4:]]
    )
    prompt = f"""Answer the question using only the document and the analysis below.
If the answer is not in the document, say it is not mentioned, then give a practical next step.
Do not invent facts.

Document:
{doc}

Context / Result:
{context}

Recent chat:
{hist}

Question: {question}

Answer:"""
    r = client.models.generate_content(model=MODEL, contents=prompt)
    return r.text.strip()

st.subheader(labels["add_doc"])

method = st.radio("Input", [labels["paste"], labels["upload"]], horizontal=True, label_visibility="collapsed")

text = ""
if method == labels["paste"]:
    text = st.text_area(
        "text",
        value=st.session_state.get("example", ""),
        height=150,
        placeholder=labels["paste_here"],
        label_visibility="collapsed"
    )
else:
    f = st.file_uploader("file", type=["pdf", "txt"], label_visibility="collapsed")
    if f:
        text = extract_text_from_pdf(f) if f.type == "application/pdf" else f.read().decode("utf-8", errors="ignore")
        if text:
            st.success("Loaded" if not is_hindi else "लोड हो गया")

if text.strip():
    st.caption(f"{len(text):,} characters" if not is_hindi else f"{len(text):,} अक्षर")

b1, b2 = st.columns(2)
with b1:
    do_saral = st.button(labels["simplify_btn"], type="primary", use_container_width=True, disabled=not text.strip())
with b2:
    do_analyse = st.button(labels["analyse_btn"], use_container_width=True, disabled=not text.strip())

if st.button(labels["reset"], use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

out_lang = labels["output_lang"]

if do_saral and text.strip():
    with st.spinner("Working…" if not is_hindi else "काम हो रहा है…"):
        try:
            st.session_state.doc = text
            st.session_state.simplified = simplify_document(text, out_lang)
            st.session_state.mode_result = "saral"
            st.session_state.chat = []
        except Exception as e:
            st.error(str(e))

if do_analyse and text.strip():
    with st.spinner("Working…" if not is_hindi else "काम हो रहा है…"):
        try:
            st.session_state.doc = text
            raw = analyse_document(text, out_lang)
            st.session_state.analyse_parts = split_analyse(raw)
            st.session_state.analyse_raw = raw
            st.session_state.mode_result = "analyse"
            st.session_state.chat = []
        except Exception as e:
            st.error(str(e))

if st.session_state.get("mode_result") == "saral" and "simplified" in st.session_state:
    with st.container(border=True):
        st.subheader(labels["simplified"])
        st.markdown(st.session_state.simplified)
        st.caption(labels["disclaimer"])
    st.download_button(labels["download"], st.session_state.simplified, "simplified.txt", "text/plain", use_container_width=True)

if st.session_state.get("mode_result") == "analyse" and "analyse_parts" in st.session_state:
    p = st.session_state.analyse_parts
    with st.container(border=True):
        st.subheader(labels["what_wrong"])
        st.warning(p.get("wrong") or "—")
        st.subheader(labels["missing"])
        st.info(p.get("missing") or "—")
        st.caption(labels["disclaimer"])
    dl = f"{labels['what_wrong']}\n{p.get('wrong','')}\n\n{labels['missing']}\n{p.get('missing','')}"
    st.download_button(labels["download"], dl, "analysis.txt", "text/plain", use_container_width=True)

if "doc" in st.session_state and st.session_state.get("mode_result"):
    st.divider()
    st.subheader(labels["ask"])

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if msg := st.chat_input(labels["ask_placeholder"]):
        st.session_state.chat.append({"role": "user", "content": msg})
        with st.chat_message("user"):
            st.write(msg)

        context = st.session_state.get("simplified", "") if st.session_state.mode_result == "saral" else st.session_state.get("analyse_raw", "")
        with st.chat_message("assistant"):
            with st.spinner("Checking..." if not is_hindi else "जांच रहे हैं..."):
                try:
                    ans = answer_from_document(st.session_state.doc, context, st.session_state.chat, msg)
                    st.write(ans)
                    st.session_state.chat.append({"role": "assistant", "content": ans})
                except Exception as e:
                    st.error(str(e))

    if st.session_state.get("chat") and st.button("Clear chat" if not is_hindi else "चैट साफ करें"):
        st.session_state.chat = []
        st.rerun()

st.divider()
st.caption("For understanding only · Not official advice" if not is_hindi else "केवल समझने के लिए · आधिकारिक सलाह नहीं")