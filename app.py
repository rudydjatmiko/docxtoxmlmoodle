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
from docx import Document
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
# TITLE
# ======================
st.title("📄 DOCX → Moodle XML Converter")
st.caption("Convert soal Word ke XML Moodle + Debug Tools")

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
col1, col2, col3, col4 = st.columns(4)

with col1:
    process_btn = st.button("🚀 Proses", use_container_width=True)

with col2:
    reset_btn = st.button("🔄 Reset", use_container_width=True)

with col3:
    debug_raw_btn = st.button("📄 RAW", use_container_width=True)

with col4:
    debug_lines_btn = st.button("🔍 Baris", use_container_width=True)

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
# SIMPAN FILE TEMP
# ======================
def save_temp(uploaded_file):
    temp_path = os.path.join(BASE_DIR, "temp.docx")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())
    return temp_path

# ======================
# DEBUG RAW (ASLI)
# ======================
if uploaded_file and debug_raw_btn:

    with st.spinner("🔍 Membaca RAW DOCX..."):

        try:
            temp_path = save_temp(uploaded_file)
            doc = Document(temp_path)

            st.subheader("📄 RAW TEXT (ASLI DOCX)")

            raw_lines = []

            for para in doc.paragraphs:
                text = para.text if para.text else "[KOSONG]"
                raw_lines.append(text)

            st.code("\n".join(raw_lines))

        except Exception as e:
            st.error(f"❌ Error RAW: {str(e)}")

# ======================
# DEBUG BARIS (HASIL READER)
# ======================
if uploaded_file and debug_lines_btn:

    with st.spinner("🔍 Membaca struktur baris..."):

        try:
            temp_path = save_temp(uploaded_file)
            elements = read_docx(temp_path)

            st.subheader("📄 Semua Baris (Processed Elements)")

            lines = []

            for i, el in enumerate(elements):
                text = el.get("text", "").strip()
                img_count = len(el.get("images", []))

                if not text:
                    text = "[KOSONG]"

                line = f"{i+1:03d} | {text}"

                if img_count > 0:
                    line += f"  🖼️({img_count})"

                # highlight ANS
                if "ANS:" in text:
                    line = "🔑 " + line

                # highlight kemungkinan pilihan
                elif len(text.split()) <= 4:
                    line = "👉 " + line

                lines.append(line)

            st.code("\n".join(lines))

        except Exception as e:
            st.error(f"❌ Error Debug: {str(e)}")

# ======================
# PROCESS
# ======================
if uploaded_file and process_btn:

    with st.spinner("🔄 Memproses DOCX → XML..."):

        try:
            temp_path = save_temp(uploaded_file)

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

    # nama file sesuai docx
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

    with st.expander("🔍 Preview XML"):
        st.code(st.session_state.xml_result[:2000], language="xml")
