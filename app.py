import streamlit as st
from docx import Document
import re
import base64
import io

# --- 1. FUNGSI HELPER ---
def wrap_arabic(text):
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 30px; line-height: 1.8;">\1</span>', text)

def get_images_from_docx(doc):
    images = []
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            try:
                img_data = rel.target_part.blob
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                images.append(img_base64)
            except:
                continue
    return images

# --- 2. FUNGSI UTAMA KONVERSI ---
def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    all_images = get_images_from_docx(doc)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    questions_xml = ""
    
    # Statistik untuk Konfirmasi
    stats = {"PG": 0, "MCS": 0, "Essay": 0}
    
    q_num = 1
    img_counter = 0 
    i = 0
    
    while i < len(lines):
        line = lines[i]

        # A. DETEKSI ESSAY
        if "Berdasarkan kisah" in line or "Tuliskan terjemahan" in line or line.upper() == "ESSAY":
            if line.upper() == "ESSAY": i += 1
            essay_content = wrap_arabic("<br/>".join(lines[i:]))
            questions_xml += f"""
  <question type="essay">
    <name><text>Soal {q_num:02d} (Essay)</text></name>
    <questiontext format="html"><text><![CDATA[<p>{essay_content}</p>]]></text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
    <responsefieldlines>15</responsefieldlines>
  </question>\n"""
            stats["Essay"] += 1
            break 

        # B. DETEKSI PILIHAN GANDA
        if not line.startswith("Ans:") and not line.isupper():
            q_text = wrap_arabic(line)
            
            # Gambar/Rumus
            img_tag = ""
            file_tag = ""
            if re.search(r'\[(Image|GAMBAR|RUMUS)\]', line, re.IGNORECASE) and img_counter < len(all_images):
                img_data = all_images[img_counter]
                img_name = f"img_{q_num}.png"
                img_tag = f'<p><img src="@@PLUGINFILE@@/{img_name}"/></p>'
                file_tag = f'<file name="{img_name}" path="/" encoding="base64">{img_data}</file>'
                img_counter += 1
                q_text = re.sub(r'\[(Image|GAMBAR|RUMUS)\]', '', q_text, flags=re.IGNORECASE).strip()

            i += 1
            choices = []
            ans_key = "A"
            
            while i < len(lines):
                if lines[i].upper().startswith("ANS:"):
                    ans_key = lines[i].replace("Ans:", "").replace("ANS:", "").strip().upper()
                    i += 1
                    break
                else:
                    choices.append(re.sub(r'^[A-E][\.:\)]\s*', '', lines[i]))
                    i += 1
            
            # Tipe Soal
            if 23 <= q_num <= 25:
                q_type = "multichoiceset"
                stats["MCS"] += 1
            else:
                q_type = "multichoice"
                stats["PG"] += 1
            
            current_q_xml = f'  <question type="{q_type}">\n'
            current_q_xml += f'    <name><text>Soal {q_num:02d}</text></name>\n'
            current_q_xml += f'    <questiontext format="html">\n      <text><![CDATA[<p>{q_text}</p>{img_tag}]]></text>\n      {file_tag}\n    </questiontext>\n'
            current_q_xml += f'    <single>{"true" if q_type=="multichoice" else "false"}</single>\n    <shuffleanswers>true</shuffleanswers>\n    <answernumbering>abc</answernumbering>\n'
            
            for idx, choice_text in enumerate(choices):
                label = chr(65 + idx)
                fraction = "100" if label in ans_key else "0"
                current_q_xml += f'    <answer fraction="{fraction}" format="html">\n      <text><![CDATA[{wrap_arabic(choice_text)}]]></text>\n      <feedback><text></text></feedback>\n    </answer>\n'
            
            current_q_xml += '  </question>\n'
            questions_xml += current_q_xml
            q_num += 1
        else:
            i += 1
            
    return xml_header + questions_xml + '</quiz>', stats

# --- 3. TAMPILAN STREAMLIT (UI) ---
st.set_page_config(page_title="Konverter Moodle Pro", page_icon="🕋")

st.title("🕋 Moodle XML Converter + Summary")
st.write("Unggah dokumen Word Anda untuk melihat ringkasan hasil konversi.")

uploaded_file = st.file_uploader("Pilih file .docx", type=["docx"])

if uploaded_file:
    with st.spinner('Menganalisis dokumen...'):
        try:
            hasil_xml, statistik = convert_docx_to_moodle_xml(uploaded_file)
            
            # TAMPILAN KONFIRMASI (SUMMARY)
            st.success("✅ Dokumen berhasil diproses!")
            
            st.markdown("### 📊 Ringkasan Hasil Konversi")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Soal", sum(statistik.values()))
            with col2:
                st.metric("Pilihan Ganda", statistik["PG"])
            with col3:
                st.metric("Multi-Response", statistik["MCS"])
            with col4:
                st.metric("Essay", statistik["Essay"])
            
            st.divider()
            
            # Pratinjau instruksi unduh
            st.info("Jika jumlah soal sudah sesuai, silakan klik tombol di bawah untuk mengunduh.")
            
            st.download_button(
                label="📥 DOWNLOAD XML MOODLE", 
                data=hasil_xml, 
                file_name="soal_siap_import.xml", 
                mime="text/xml",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

st.caption("Pastikan format soal sesuai panduan agar statistik muncul dengan akurat.")
