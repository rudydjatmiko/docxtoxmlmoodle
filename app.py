import streamlit as st
from core.docx_reader import read_docx
from parser import run_parser
from core.builder import build_xml

st.title("DOCX → Moodle XML Converter")

uploaded_file = st.file_uploader("Upload file DOCX", type=["docx"])

if uploaded_file:
    with open("temp.docx", "wb") as f:
        f.write(uploaded_file.read())

    st.success("File uploaded!")

    # PROCESS
    elements = read_docx("temp.docx")
    questions = run_parser(elements)
    xml = build_xml(questions)

    st.download_button(
        label="Download XML",
        data=xml,
        file_name="result.xml",
        mime="text/xml"
    )
