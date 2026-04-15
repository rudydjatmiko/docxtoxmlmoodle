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
from core.docx_reader import read_docx
from parser import run_parser
from core.builder import build_xml

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="DOCX to XML", layout="centered")

st.title("DOCX → XML")

# ======================
# STATE
# ======================
if "xml_result" not in st.session_state:
    st.session_state.xml_result = None

# ======================
# UPLOAD
# ======================
uploaded_file = st.file_uploader("", type=["docx"])

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
# RAW (python-docx)
# ======================
if uploaded_file and raw_btn:
    try:
        path = save_temp(uploaded_file)
        doc = Document(path)

        lines = [p.text for p in doc.paragraphs]
        st.code("\n".join(lines))

    except Exception as e:
        st.error(str(e))

# ======================
# XML RAW (ASLI DOCX)
# ======================
if uploaded_file and xml_btn:
    try:
        import zipfile

        path = save_temp(uploaded_file)

        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")

        st.code(xml)

    except Exception as e:
        st.error(str(e))

# ======================
# PROCESS
# ======================
if uploaded_file and process_btn:
    try:
        path = save_temp(uploaded_file)

        elements = read_docx(path)
        questions = run_parser(elements)
        xml = build_xml(questions)

        st.session_state.xml_result = xml

    except Exception as e:
        st.error(str(e))

# ======================
# RESULT
# ======================
if st.session_state.xml_result:

    name = os.path.splitext(uploaded_file.name)[0] + ".xml"

    st.download_button(
        "Download XML",
        data=st.session_state.xml_result,
        file_name=name,
        mime="text/xml"
    )

    with st.expander("Preview"):
        st.code(st.session_state.xml_result[:2000])
