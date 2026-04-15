import sys
import os

# ======================
# FIX PATH (KUNCI UTAMA)
# ======================
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

# ======================
# IMPORT
# ======================
import streamlit as st
from core.docx_reader import read_docx
from parser import run_parser
from core.builder import build_xml

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="DOCX to Moodle XML", layout="centered")

st.title("📄 DOCX → Moodle XML Converter")
st.caption("Convert soal Word ke XML Moodle")

# ======================
# STATE
# ======================
if "xml_result" not in st.session_state:
    st.session_state.xml_result = None

# ======================
# UPLOAD
# ======================
uploaded_file = st.file_uploader("Upload DOCX", type=["docx"])

col1, col2 = st.columns(2)

process_btn = col1.button("🚀 Proses", use_container_width=True)
reset_btn = col2.button("🔄 Reset", use_container_width=True)

# ======================
# RESET
# ======================
if reset_btn:
    st.session_state.xml_result = None
    temp_path = os.path.join(BASE_DIR, "temp.docx")
    if os.path.exists(temp_path):
        os.remove(temp_path)
    st.rerun()

# ======================
# PROCESS
# ======================
if uploaded_file and process_btn:
    with st.spinner("Processing..."):
        try:
            temp_path = os.path.join(BASE_DIR, "temp.docx")

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            elements = read_docx(temp_path)
            questions = run_parser(elements)
            xml = build_xml(questions)

            st.session_state.xml_result = xml

        except Exception as e:
            st.error(str(e))

# ======================
# RESULT
# ======================
if st.session_state.xml_result:
    st.success("✅ Selesai!")

    st.download_button(
        "⬇️ Download XML",
        data=st.session_state.xml_result,
        file_name="moodle.xml",
        mime="text/xml"
    )

    with st.expander("Preview"):
        st.code(st.session_state.xml_result[:2000], language="xml")
