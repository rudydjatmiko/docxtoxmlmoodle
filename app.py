import sys
import os

# ======================
# FIX PATH
# ======================
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

# ======================
# IMPORT
# ======================
import streamlit as st
from docx import Document
import zipfile

from parser import run_parser
from core.builder import build_xml

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="DOCX to XML", layout="centered")

st.title("DOCX → XML Moodle")

# ======================
# STATE
# ======================
if "xml_result" not in st.session_state:
    st.session_state.xml_result = None

# ======================
# UPLOAD (WAJIB DI ATAS)
# ======================
uploaded_file = st.file_uploader("", type=["docx"])

# ======================
# HELPER
# ======================
def save_temp(file):
    path = os.path.join(BASE_DIR, "temp.docx")
    with open(path, "wb") as f:
        f.write(file.read())
    return path

# ======================
# BUTTON
# ======================
col1, col2, col3 = st.columns(3)

process_btn = col1.button("Proses")
raw_btn = col2.button("RAW")
xml_btn = col3.button("XML")

# ======================
# DEBUG RAW (python-docx)
# ======================
if uploaded_file is not None and raw_btn:
    try:
        path = save_temp(uploaded_file)
        doc = Document(path)

        lines = [p.text for p in doc.paragraphs]
        st.text_area("", "\n".join(lines), height=500)

    except Exception as e:
        st.error(str(e))

# ======================
# DEBUG XML (ASLI DOCX)
# ======================
if uploaded_file is not None and xml_btn:
    try:
        path = save_temp(uploaded_file)

        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")

        # tampilkan apa adanya (tanpa tambahan)
        st.text_area("", xml, height=500)

    except Exception as e:
        st.error(str(e))

# ======================
# PROCESS
# ======================
if uploaded_file is not None and process_btn:
    try:
        path = save_temp(uploaded_file)

        questions = run_parser(path)
        xml_output = build_xml(questions)

        st.session_state.xml_result = xml_output

    except Exception as e:
        st.error(str(e))

# ======================
# RESULT
# ======================
if st.session_state.xml_result:

    file_name = os.path.splitext(uploaded_file.name)[0] + ".xml"

    st.download_button(
        "Download XML",
        data=st.session_state.xml_result,
        file_name=file_name,
        mime="text/xml"
    )

    # preview tetap minimal
    with st.expander("Preview"):
        st.text_area("", st.session_state.xml_result, height=400)
