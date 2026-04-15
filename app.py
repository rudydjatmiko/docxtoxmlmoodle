import sys
import os

# ======================
# FIX PATH (WAJIB)
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
st.set_page_config(
    page_title="DOCX to Moodle XML",
    page_icon="📄",
    layout="centered"
)

# ======================
# STYLE
# ======================
st.markdown("""
<style>
.block {
    padding: 1rem;
    border-radius: 10px;
    background-color: #f8f9fa;
    border: 1px solid #ddd;
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
    "Upload file",
    type=["docx"],
    label_visibility="collapsed"
)

# ======================
# BUTTONS
# ======================
col1, col2, col3 = st.columns(3)

with col1:
    process_btn = st.button("🚀 Proses", use_container_width=True)

with col2:
    reset_btn = st.button("🔄 Reset", use_container_width=True)

with col3:
    debug_btn = st.button("🔍 Debug DOCX", use_container_width=True)

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
# DEBUG DOCX
# ======================
if uploaded_file and debug_btn:

    with st.spinner("🔍 Membaca struktur DOCX..."):

        try:
            temp_path = os.path.join(BASE_DIR, "temp.docx")

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            elements = read_docx(temp_path)

            st.subheader("📄 Hasil Pembacaan DOCX")

            for i, el in enumerate(elements):
                st.markdown(f"### 🔹 Paragraf {i+1}")

                st.write("Text:")
                st.code(el.get("text", ""))

                img_count = len(el.get("images", []))
                st.write(f"Jumlah gambar: {img_count}")

                if img_count > 0:
                    st.success("✔ Ada gambar di paragraf ini")

                # debug detail (opsional)
                with st.expander("Detail JSON"):
                    st.json(el)

        except Exception as e:
            st.error(f"❌ Error Debug: {str(e)}")

# ======================
# PROCESS
# ======================
if uploaded_file and process_btn:

    with st.spinner("🔄 Memproses file..."):

        try:
            temp_path = os.path.join(BASE_DIR, "temp.docx")

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            # PIPELINE
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

    st.success("✅ Konversi berhasil!")

    # nama file xml sesuai docx
    original_name = uploaded_file.name
    base_name = os.path.splitext(original_name)[0]
    xml_filename = base_name + ".xml"

    st.download_button(
        label="⬇️ Download XML",
        data=st.session_state.xml_result,
        file_name=xml_filename,
        mime="text/xml",
        use_container_width=True
    )

    # preview
    with st.expander("🔍 Preview XML"):
        st.code(st.session_state.xml_result[:2000], language="xml")
