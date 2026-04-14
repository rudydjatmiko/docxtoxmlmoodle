import streamlit as st
from parser import parse_docx_to_moodle
from debug_parser import debug_docx
from xml_viewer import parse_xml_questions, render_all_questions

st.set_page_config(page_title="Parser", layout="wide")

st.title("📄 DOCX → Moodle XML")

# =========================
# 🔥 TOP CONTROL (SEJAJAR)
# =========================
colA, colB = st.columns(2)

with colA:
    debug_mode = st.checkbox("🧪 Debug Mode")

with colB:
    moodle_version = st.selectbox(
        "🎯 Versi Multiple Choice",
        ["Default Multiple Choice", "All or Nothing Multiple Choice"]
    )

# =========================
# 🔥 MAPPING KE ENGINE
# =========================
if moodle_version == "All or Nothing Multiple Choice":
    moodle_type = "multichoiceset"
    st.info("⚠️ Pastikan plugin All-or-Nothing sudah terinstall di Moodle")
else:
    moodle_type = "multichoice"

# DEBUG (opsional)
# st.caption(f"Engine type: {moodle_type}")

# =========================
# FILE UPLOAD
# =========================
file = st.file_uploader("Upload DOCX", type="docx")

# =========================
# DOCX PARSER
# =========================
if file:

    if debug_mode:
        logs = debug_docx(file)

        st.warning("DEBUG MODE")

        with st.expander("Lihat Debug"):
            for l in logs:
                st.text(l)

    else:
        try:
            xml, stats, logs, title = parse_docx_to_moodle(
                file,
                moodle_type=moodle_type   # 🔥 FIX DI SINI
            )

            st.success(title)

            # =========================
            # STATISTIK
            # =========================
            col1, col2, col3 = st.columns(3)
            col1.metric("PG", stats["MULTIPLE CHOICE"])
            col2.metric("PG Kompleks", stats["MULTIPLE CHOICE SET"])
            col3.metric("Essay", stats["ESSAY"])

            # =========================
            # DOWNLOAD XML
            # =========================
            filename = file.name.replace(".docx", ".xml")

            st.download_button(
                "📥 Download XML",
                xml,
                file_name=filename,
                mime="text/xml"
            )

            # =========================
            # 🔥 PREVIEW XML
            # =========================
            st.markdown("## 👁️ Preview XML (hasil konversi)")

            try:
                questions = parse_xml_questions(xml)
                render_all_questions(questions)
            except Exception as e:
                st.error(f"Gagal preview XML: {e}")

        except Exception as e:
            st.error(f"❌ Error parsing: {e}")

# =========================
# XML VIEWER
# =========================
st.markdown("---")
st.markdown("## 📂 XML Viewer (Upload File XML)")

xml_file = st.file_uploader("Upload XML Moodle", type="xml", key="xml_view")

if xml_file:
    try:
        xml_content = xml_file.read().decode("utf-8")
        questions = parse_xml_questions(xml_content)
        render_all_questions(questions)
    except Exception as e:
        st.error(f"Gagal membaca XML: {e}")
