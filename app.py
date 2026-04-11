import streamlit as st
from parser import parse_docx_to_moodle

# --- 1. SETTING UI & HEADER ---
st.set_page_config(page_title="Docx to XML Moodle", page_icon="📝", layout="wide")

# Menggunakan kolom untuk menampilkan ikon secara berdampingan
col_title, col_icons = st.columns([3, 1])

with col_title:
    st.title("🌙 Moodle XML Parser")
    st.write("Convert **MS Word** file format to **Moodle XML**")

with col_icons:
    # Menampilkan ikon MS Word dan Moodle menggunakan Emoji besar atau URL Gambar
    # Jika Anda punya file lokal, ganti URL dengan nama file
    st.markdown("### 🟦 ➡️ 🟧") 
    st.caption("MS Word to Moodle")

st.markdown("---")

# --- 2. KOMPONEN UGGAH FILE ---
# Menambahkan ikon pada area uploader
st.info("💡 **Petunjuk:** Pastikan file .docx Anda mengikuti format yang ditentukan.")
uploaded_file = st.file_uploader("📂 Upload your MS Word File (.docx)", type="docx")

if uploaded_file:
    # Komunikasi dengan parser.py
    with st.spinner("⏳ Sedang memproses data..."):
        xml_data, stats, logs, judul = parse_docx_to_moodle(uploaded_file)
    
    if xml_data:
        st.success(f"✅ **File Terdeteksi:** {judul}")
        
        # --- 3. DASHBOARD STATISTIK DENGAN IKON ---
        st.write("### 📊 Ringkasan Data")
        c1, c2, c3 = st.columns(3)
        
        # Menggunakan emoji sebagai ikon representatif
        c1.metric("📝 PG Biasa", stats.get("MULTIPLE CHOICE", 0))
        c2.metric("📑 PG Kompleks", stats.get("MULTIPLE CHOICE SET", 0))
        c3.metric("✍️ Soal Essay", stats.get("ESSAY", 0))
        
        st.markdown("---")
        
        # --- 4. TOMBOL DOWNLOAD DENGAN IKON ---
        # Menempatkan tombol download di posisi yang menonjol
        st.download_button(
            label="📥 Klik di Sini untuk Unduh XML Moodle",
            data=xml_data,
            file_name=f"{uploaded_file.name}.xml",
            mime="text/xml",
            use_container_width=True
        )
    else:
        st.error("❌ Gagal mendeteksi soal. Silakan periksa format dokumen Anda.")

# --- 5. FOOTER ---
st.markdown("<br><hr><center>Made with ❤️ for Educators</center>", unsafe_allow_html=True)
