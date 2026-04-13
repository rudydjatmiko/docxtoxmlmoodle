import streamlit as st
from parser import parse_docx_to_moodle
from debug_parser import debug_docx

st.set_page_config(page_title="Parser", layout="wide")

st.title("📄 DOCX → Moodle XML")

debug_mode = st.checkbox("🧪 Debug Mode")

file = st.file_uploader("Upload DOCX", type="docx")

if file:

    if debug_mode:
        logs = debug_docx(file)

        st.warning("DEBUG MODE")

        with st.expander("Lihat Debug"):
            for l in logs:
                st.text(l)

    else:
        xml, stats, logs, title = parse_docx_to_moodle(file)

        st.success(title)

        col1, col2, col3 = st.columns(3)
        col1.metric("PG", stats["MULTIPLE CHOICE"])
        col2.metric("PG Kompleks", stats["MULTIPLE CHOICE SET"])
        col3.metric("Essay", stats["ESSAY"])

        st.download_button("Download XML", xml, file_name="quiz.xml")
