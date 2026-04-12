import streamlit as st
from parser import parse_docx_to_moodle

# --- 1. SETTING UI & HEADER ---
st.set_page_config(page_title="Docx to XML Moodle", page_icon="📝", layout="wide")

col_title, col_icons = st.columns([3, 1])

with col_title:
    st.title("🌙 Moodle XML Parser")
    st.write("Convert **MS Word** file format to **Moodle XML**")

with col_icons:
    st.markdown("### 🟦 ➡️ 🟧") 
    st.caption("MS Word to Moodle")

st.markdown("---")

# --- 2. KOMPONEN UNGGAH FILE ---
st.info("💡 **Petunjuk:** Berikan satu baris kosong sebelum kata MULTIPLECHOICE, MULTIPLEANSWER, atau ESSAY di file Word Anda.")
uploaded_file = st.file_uploader("📂 Upload your MS Word File (.docx)", type="docx")

if uploaded_file:
    # Komunikasi dengan parser.py
    with st.spinner("⏳ Sedang memproses data dengan doc2python..."):
        xml_data, stats, logs, judul = parse_docx_to_moodle(uploaded_file)
    
    if xml_data:
        st.success(f"✅ **File Terdeteksi:** {judul}")
        
        # --- 3. DASHBOARD STATISTIK (DISINKRONKAN) ---
        st.write("### 📊 Ringkasan Data")
        c1, c2, c3 = st.columns(3)
        
        # PERBAIKAN: Kunci stats disesuaikan dengan parser.py terbaru
        c1.metric("📝 PG Biasa", stats.get("MULTIPLE CHOICE", 0))
        c2.metric("📑 PG Kompleks", stats.get("MULTIPLE ANSWER", 0)) # Diubah dari MULTIPLE CHOICE SET
        c3.metric("✍️ Soal Essay", stats.get("ESSAY", 0))
        
        # Menampilkan Audit Log jika ada error/catatan
        if logs:
            with st.expander("🔍 Lihat Detail Audit Log"):
                for log in logs:
                    st.write(log)
        
        st.markdown("---")
        
        # --- 4. TOMBOL DOWNLOAD ---
        st.download_button(
            label="📥 Klik di Sini untuk Unduh XML Moodle",
            data=xml_data,
            file_name=f"{uploaded_file.name}.xml",
            # Menggunakan encoding utf-8 agar teks Arab aman
            mime="text/xml",
            use_container_width=True
        )
    else:
        # Jika xml_data None, judul biasanya berisi pesan error dari try-except di parser
        st.error(f"❌ Gagal memproses: {judul}")

# --- 5. FOOTER ---
st.markdown("<br><hr><center>Made with ❤️ for Educators | v2.0 (doc2python)</center>", unsafe_allow_html=True)
