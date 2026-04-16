import streamlit as st
from parser import run_parser
from core.builder import build_xml

st.set_page_config(page_title="DOCX to XML Moodle", layout="wide")

st.title("📄 DOCX → XML Moodle Converter")

uploaded = st.file_uploader("Upload file DOCX", type=["docx"])

col1, col2, col3 = st.columns(3)

process_btn = col1.button("🚀 Convert")
debug_btn = col2.button("🐞 Debug")
reset_btn = col3.button("🔄 Reset")

if reset_btn:
    st.experimental_rerun()

if uploaded and process_btn:

    with open("temp.docx", "wb") as f:
        f.write(uploaded.read())

    questions, elements = run_parser("temp.docx")

    # ======================
    # STATISTIK
    # ======================
    mc = 0
    multi = 0
    essay = 0

    for q in questions:
        if q["type"] == "ESSAY":
            essay += 1
        elif q["type"] == "MC":
            if len(q["answers"]) > 1:
                multi += 1
            else:
                mc += 1

    st.success(f"MC: {mc} | Multi: {multi} | Essay: {essay}")

    xml = build_xml(questions)

    st.download_button(
        "⬇️ Download XML",
        xml,
        file_name=uploaded.name.replace(".docx", ".xml")
    )

    st.code(xml, language="xml")

# ======================
# DEBUG RAW
# ======================
if uploaded and debug_btn:

    with open("temp.docx", "wb") as f:
        f.write(uploaded.read())

    _, elements = run_parser("temp.docx")

    st.subheader("🐞 RAW SCAN (Hybrid Reader)")

    for i, el in enumerate(elements):
        st.text(f"{i+1:03d} | L{el['level']} | {el['text']}")
