import sys
import os

# ======================
# FIX IMPORT PATH (WAJIB)
# ======================
BASE_DIR = os.path.dirname(__file__)

sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "core"))
sys.path.append(os.path.join(BASE_DIR, "models"))
sys.path.append(os.path.join(BASE_DIR, "processors"))
sys.path.append(os.path.join(BASE_DIR, "utils"))

# ======================
# IMPORT MODULE
# ======================
import streamlit as st
from core.docx_reader import read_docx
from parser import run_parser
from core.builder import build_xml

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="DOCX to Moodle XML",
    page_icon="📄",
    layout="centered"
)

# ======================
# SIMPLE CSS (RINGAN)
# ======================
st.markdown("""
<style>
.box {
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid #ddd;
    background-color: #f9f9f9;
}
.success {
    padding: 1rem;
    border-radius: 8px;
    background-color: #e6f4ea;
    color: #1e7e34;
}
</style>
""", unsafe_allow_html=True)

# ======================
# TITLE
# ======================
st.title("📄 DOCX → Moodle XML Converter")
st.caption("Convert soal Word ke XML Moodle (Auto MC & Multiple Response)")

# ======================
# SESSION STATE
# ======================
if "xml_result" not in st.session_state:
    st.session_state.xml_result = None

# ======================
# UPLOAD
# ======================
st.markdown("### 📥 Upload File DOCX")

uploaded_file = st.file_uploader(
    "Pilih file",
    type=["docx"],
    label_visibility="collapsed"
)

# ======================
# BUTTONS
# ======================
col1, col2 = st.columns(2)

with col1:
    process_btn = st.button("🚀 Proses", use_container_width=True)

with col2:
    reset_btn = st.button("🔄 Reset", use_container_width=True)

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

    with st.spinner("🔄 Memproses file..."):

        try:
            # simpan file sementara
            temp_path = os.path.join(BASE_DIR, "temp.docx")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            # pipeline
            elements = read_docx(temp_path)
            questions = run_parser(elements)
            xml = build_xml(questions)

            st.session_state.xml_result = xml

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ======================
# RESULT
# ======================
if st.session_state.xml_result:

    st.markdown(
        '<div class="success">✅ Konversi berhasil!</div>',
        unsafe_allow_html=True
    )

    st.download_button(
        label="⬇️ Download XML",
        data=st.session_state.xml_result,
        file_name="moodle.xml",
        mime="text/xml",
        use_container_width=True
    )

    # preview (debug ringan)
    with st.expander("🔍 Preview XML"):
        st.code(st.session_state.xml_result[:2000], language="xml")
