import streamlit as st
from parser import parse_docx_to_moodle

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Moodle XML Converter",
    page_icon="📝",
    layout="wide"
)

# =========================
# HEADER
# =========================
col1, col2 = st.columns([4,1])

with col1:
    st.title("🌙 Moodle XML Converter")
    st.caption("Convert MS Word (.docx) → Moodle XML")

with col2:
    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

st.divider()

# =========================
# UPLOAD
# =========================
st.info("💡 Pastikan file yang diupload berupa file docx dengan format ANS, memiliki tipe soal (MULTIPLE CHOICE, atau ESSAY), disertai kunci jawaban ANS: ...")

uploaded_file = st.file_uploader(
    "📂 Upload file DOCX",
    type="docx"
)

# =========================
# PROCESS
# =========================
if uploaded_file:

    with st.spinner("⏳ Memproses file..."):
        xml_data, stats, logs, judul = parse_docx_to_moodle(uploaded_file)

    if xml_data:

        # =========================
        # SUCCESS INFO
        # =========================
        st.success(f"✅ File: **{judul}**")

        # =========================
        # DASHBOARD
        # =========================
        st.subheader("📊 Statistik Soal")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                label="📝 PG Biasa",
                value=stats.get("MULTIPLE CHOICE", 0)
            )

        with c2:
            st.metric(
                label="📑 PG Kompleks",
                value=stats.get("MULTIPLE CHOICE SET", 0)
            )

        with c3:
            st.metric(
                label="✍️ Essay",
                value=stats.get("ESSAY", 0)
            )

        st.divider()

        # =========================
        # ACTION BUTTON
        # =========================
        st.subheader("⬇️ Download")

        st.download_button(
            label="📥 Download XML Moodle",
            data=xml_data,
            file_name=uploaded_file.name.replace(".docx", ".xml"),
            mime="text/xml",
            use_container_width=True
        )

        # =========================
        # LOG
        # =========================
        if logs:
            st.divider()
            with st.expander("🔍 Audit Log (Klik untuk melihat detail)"):
                for log in logs:
                    st.write(log)

    else:
        st.error(f"❌ Gagal memproses file\n\n{judul}")

# =========================
# FOOTER
# =========================
st.divider()
st.caption("Made with ❤️ for Educators")
