import streamlit as st
from docxtoxmlmoodle.core.docx_reader import read_docx
from docxtoxmlmoodle.parser import run_parser
from docxtoxmlmoodle.core.builder import build_xml
import os

st.set_page_config(page_title="DOCX to Moodle XML", layout="centered")

# =====================
# STYLE (LIGHTWEIGHT)
# =====================
st.markdown("""
<style>
.block {
    padding: 1.2rem;
    border-radius: 10px;
    background-color: #f8f9fa;
    border: 1px solid #e0e0e0;
}
.success-box {
    padding: 1rem;
    border-radius: 8px;
    background-color: #e6f4ea;
    color: #1e7e34;
}
</style>
""", unsafe_allow_html=True)

# =====================
# TITLE
# =====================
st.title("📄 DOCX → Moodle XML Converter")
st.caption("Convert soal Word ke format XML Moodle (auto MC & multiple response)")

# =====================
# SESSION STATE
# =====================
if "xml" not in st.session_state:
    st.session_state.xml = None

# =====================
# FILE UPLOAD
# =====================
st.markdown("### 📥 Upload File")

uploaded_file = st.file_uploader(
    "Pilih file DOCX",
    type=["docx"],
    label_visibility="collapsed"
)

# =====================
# PROCESS BUTTON
# =====================
col1, col2 = st.columns([1,1])

with col1:
    process_btn = st.button("🚀 Proses", use_container_width=True)

with col2:
    reset_btn = st.button("🔄 Reset", use_container_width=True)

# =====================
# RESET LOGIC
# =====================
if reset_btn:
    st.session_state.xml = None
    if os.path.exists("temp.docx"):
        os.remove("temp.docx")
    st.rerun()

# =====================
# PROCESSING
# =====================
if uploaded_file and process_btn:

    with st.spinner("🔄 Memproses file..."):

        # simpan file sementara
        with open("temp.docx", "wb") as f:
            f.write(uploaded_file.read())

        try:
            elements = read_docx("temp.docx")
            questions = run_parser(elements)
            xml = build_xml(questions)

            st.session_state.xml = xml

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# =====================
# HASIL
# =====================
if st.session_state.xml:

    st.markdown('<div class="success-box">✅ Konversi berhasil!</div>', unsafe_allow_html=True)

    st.download_button(
        label="⬇️ Download XML",
        data=st.session_state.xml,
        file_name="result.xml",
        mime="text/xml",
        use_container_width=True
    )

    with st.expander("🔍 Preview XML"):
        st.code(st.session_state.xml[:2000], language="xml")
