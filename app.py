import streamlit as st
from parser import parse_docx_to_moodle

# Blok Tampilan: Pengaturan Header dan UI
st.set_page_config(page_title="Moodle Parser", page_icon="🌙")
st.title("🌙 Moodle XML Parser")
st.subheader("Konverter Otomatis Soal Akidah Akhlak")

# Blok Tampilan: Komponen Unggah File
uploaded_file = st.file_uploader("Upload File DOCX Anda di sini", type="docx")

if uploaded_file:
    # Komunikasi dengan parser.py
    with st.spinner("Sedang memproses data..."):
        xml_data, stats, logs, judul = parse_docx_to_moodle(uploaded_file)
    
    if xml_data:
        # Blok Tampilan: Feedback Berhasil dan Nama Paket
        st.success(f"Berhasil Memproses: {judul}")
        
        # Blok Tampilan: Dashboard Statistik
        c1, c2, c3 = st.columns(3)
        c1.metric("Pilihan Ganda", stats.get("MULTIPLE CHOICE", 0))
        c2.metric("PG Kompleks", stats.get("MULTIPLE CHOICE SET", 0))
        c3.metric("Essay", stats.get("ESSAY", 0))
        
        # Blok Tampilan: Tombol Unduh Hasil Konversi
        st.download_button(
            label="📥 Download Hasil XML Moodle",
            data=xml_data,
            file_name=f"{uploaded_file.name}.xml",
            mime="text/xml",
            use_container_width=True
        )
    else:
        st.error("Gagal mendeteksi soal. Periksa kembali format dokumen Anda.")
