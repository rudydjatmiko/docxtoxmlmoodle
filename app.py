import streamlit as st
from docx import Document
import re
import base64

def wrap_arabic(text):
    # Regex untuk mendeteksi karakter Arab
    arabic_pattern = re.compile(r'([\u0600-\u06FF]+)')
    # Bungkus teks arab dengan span style otomatis
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\'; font-size: 30px;">\1</span>', text)

def create_xml(docx_file):
    doc = Document(docx_file)
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    # Logika ekstraksi teks dari docx ke format XML Moodle
    # (Di sini Anda memproses paragraf demi paragraf)
    
    xml_content += '</quiz>'
    return xml_content

st.title("Docx to Moodle XML Converter")
st.write("Upload file soal .docx Anda di bawah ini:")

uploaded_file = st.file_uploader("Pilih file Word", type=["docx"])

if uploaded_file:
    xml_output = create_xml(uploaded_file)
    st.download_button(
        label="Download Moodle XML",
        data=xml_output,
        file_name="soal_moodle.xml",
        mime="application/xml"
    )