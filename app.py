import streamlit as st
from parser import parse_docx_to_moodle

st.set_page_config(page_title="Docx to XML Moodle", page_icon="📝", layout="wide")

col_title, col_icons = st.columns([3, 1])

with col_title:
    st.title("🌙 Moodle XML Parser")
    st.write("Convert **MS Word (.docx)** to **Moodle XML**")

with col_icons:
    st.markdown("### 🟦 ➡️ 🟧")
    st.caption("Word → Moodle")

st.markdown("---")

st.info("💡 Pastikan setiap soal memiliki kunci jawaban (ANS).")

uploaded_file = st.file_uploader("📂 Upload file DOCX", type="docx")

if uploaded_file:
    with st.spinner("⏳ Sedang memproses file..."):
        xml_data, stats, logs, judul = parse_docx_to_moodle(uploaded_file)

    if xml_data:
        st.success(f"✅ File terdeteksi: {judul}")

        st.write("### 📊 Statistik Soal")
        c1, c2, c3 = st.columns(3)

        c1.metric("📝 PG Biasa", stats.get("MULTIPLE CHOICE", 0))
        c2.metric("📑 PG Kompleks", stats.get("MULTIPLE CHOICE SET", 0))
        c3.metric("✍️ Essay", stats.get("ESSAY", 0))

        if logs:
            with st.expander("🔍 Audit Log"):
                for log in logs:
                    st.write(log)

        st.markdown("---")

        st.download_button(
            label="📥 Download XML Moodle",
            data=xml_data,
            file_name=uploaded_file.name.replace(".docx", ".xml"),
            mime="text/xml",
            use_container_width=True
        )

    else:
        st.error(f"❌ Gagal memproses file.\n\nDetail: {judul}")

st.markdown("<br><hr><center>Made with ❤️ for Educators</center>", unsafe_allow_html=True)
