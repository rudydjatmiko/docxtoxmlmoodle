import streamlit as st
from processor import to_html
from moodle_xml import to_moodle_xml

st.set_page_config(layout="wide", page_title="Word to Moodle XML")

def main():
    st.title("🚀 Docx to Moodle XML Converter")
    st.write("Upload file soal (.docx), lihat pratinjau, lalu unduh format XML Moodle.")

    uploaded_file = st.sidebar.file_uploader("Pilih file Word", type=['docx'])

    if uploaded_file:
        # Layout 2 kolom: Kiri (Preview), Kanan (Control)
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🖥️ Monitor Preview")
            html_preview = to_html(uploaded_file)
            st.components.v1.html(html_preview, height=700, scrolling=True)

        with col2:
            st.subheader("⚙️ Opsi Konversi")
            if st.button("Generate Moodle XML"):
                with st.spinner("Memproses XML..."):
                    xml_data = to_moodle_xml(uploaded_file)
                    
                    st.success("XML Berhasil Dibuat!")
                    st.download_button(
                        label="📥 Download Moodle XML",
                        data=xml_data,
                        file_name="moodle_quiz.xml",
                        mime="application/xml"
                    )
                    
                    with st.expander("Lihat Struktur XML"):
                        st.code(xml_data.decode("utf-8"), language="xml")
    else:
        st.info("Menunggu upload file...")

if __name__ == "__main__":
    main()
