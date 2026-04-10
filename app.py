import streamlit as st
from docx import Document
import re
import base64

# --- 1. FUNGSI PENDUKUNG (BACKEND) ---

def wrap_arabic(text):
    """Mendeteksi teks Arab dan memberikan styling font besar."""
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 30px; line-height: 1.8;">\1</span>', text)

def get_images_from_docx(doc):
    """Mengekstrak gambar dari file docx."""
    images = []
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            try:
                img_data = rel.target_part.blob
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                images.append(img_base64)
            except: continue
    return images

def convert_docx_to_moodle_xml(docx_file):
    """Fungsi inti konversi dengan logika deteksi otomatis."""
    doc = Document(docx_file)
    all_images = get_images_from_docx(doc)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    questions_xml = ""
    stats = {"PG": 0, "MCS": 0, "Essay": 0, "Gambar": 0}
    
    q_num = 1
    img_idx = 0 
    i = 0
    
    while i < len(lines):
        line = lines[i]

        # A. DETEKSI ESSAY
        if line.upper() == "ESSAY" or "KERJEKAN SOAL BERIKUT" in line.upper():
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

        # B. DETEKSI PILIHAN GANDA / MULTIPLE RESPONSE
        if not line.upper().startswith("ANS:") and not line.isupper():
            q_text = wrap_arabic(line)
            
            # Cek Gambar/Rumus
            img_tag = ""
            file_tag = ""
            if re.search(r'\[(Image|GAMBAR|RUMUS)\]', line, re.IGNORECASE) and img_idx < len(all_images):
                img_data = all_images[img_idx]
                img_name = f"img_{q_num}.png"
                img_tag = f'<p><img src="@@PLUGINFILE@@/{img_name}"/></p>'
                file_tag = f'<file name="{img_name}" path="/" encoding="base64">{img_data}</file>'
                img_idx += 1
                stats["Gambar"] += 1
                q_text = re.sub(r'\[(Image|GAMBAR|RUMUS)\]', '', q_text, flags=re.IGNORECASE).strip()

            i += 1
            choices = []
            ans_key = ""
            
            # Ambil Pilihan Jawaban
            while i < len(lines):
                if lines[i].upper().startswith("ANS:"):
                    ans_key = lines[i].upper().replace("ANS:", "").strip()
                    i += 1
                    break
                else:
                    # Bersihkan label A. B. C. manual
                    choices.append(re.sub(r'^[A-E][\.:\)]\s*', '', lines[i]))
                    i += 1
            
            # LOGIKA DETEKSI TIPE SOAL (CERDAS)
            # Jika ada koma di kunci (A,B) atau kata "Pilih" di soal, maka MCS
            is_mcs = "," in ans_key or "PILIH" in q_text.upper()
            q_type = "multichoiceset" if is_mcs else "multichoice"
            
            if is_mcs: stats["MCS"] += 1
            else: stats["PG"] += 1
            
            # Bangun XML
            current_q = f'  <question type="{q_type}">\n'
            current_q += f'    <name><text>Soal {q_num:02d}</text></name>\n'
            current_q += f'    <questiontext format="html">\n      <text><![CDATA[<p>{q_text}</p>{img_tag}]]></text>\n      {file_tag}\n    </questiontext>\n'
            current_q += f'    <single>{"false" if is_mcs else "true"}</single>\n    <shuffleanswers>true</shuffleanswers>\n    <answernumbering>abc</answernumbering>\n'
            
            # Proses Jawaban
            for idx, c_text in enumerate(choices):
                label = chr(65 + idx)
                if is_mcs:
                    correct_list = [x.strip() for x in ans_key.split(',')]
                    # Skor dibagi rata untuk jawaban benar
                    fraction = str(100 // len(correct_list)) if label in correct_list else "0"
                else:
                    fraction = "100" if label == ans_key else "0"
                
                current_q += f'    <answer fraction="{fraction}" format="html">\n      <text><![CDATA[{wrap_arabic(c_text)}]]></text>\n      <feedback><text></text></feedback>\n    </answer>\n'
            
            current_q += '  </question>\n'
            questions_xml += current_q
            q_num += 1
        else:
            i += 1
            
    return xml_header + questions_xml + '</quiz>', stats

# --- 2. TAMPILAN ANTARMUKA (UI STREAMLIT) ---

st.set_page_config(page_title="Moodle Converter Pro", page_icon="📝")

st.title("📝 Moodle XML Converter Pro")
st.markdown("Konversi soal .docx Anda ke Moodle XML secara akurat dan otomatis.")

uploaded_file = st.file_uploader("Upload file soal .docx", type=["docx"])

if uploaded_file:
    # Dinamisasi Nama File
    nama_xml = re.sub(r'\.docx$', '.xml', uploaded_file.name, flags=re.IGNORECASE)
    if not nama_xml.endswith('.xml'): nama_xml += '.xml'

    with st.spinner('Menganalisis file...'):
        try:
            hasil_xml, statistik = convert_docx_to_moodle_xml(uploaded_file)
            
            st.success(f"Berhasil memproses: {uploaded_file.name}")
            
            # Dashboard Statistik
            st.subheader("📊 Ringkasan Konversi")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Soal", statistik["PG"] + statistik["MCS"] + statistik["Essay"])
            c2.metric("Pilihan Ganda", statistik["PG"])
            c3.metric("Multi-Response", statistik["MCS"])
            c4.metric("Essay", statistik["Essay"])
            
            if statistik["Gambar"] > 0:
                st.info(f"🖼️ Terdeteksi {statistik['Gambar']} gambar/rumus.")

            st.divider()

            # Tombol Download
            st.download_button(
                label=f"📥 DOWNLOAD {nama_xml.upper()}", 
                data=hasil_xml, 
                file_name=nama_xml, 
                mime="text/xml",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"Gagal mengonversi: {e}")

st.caption("Pastikan format kunci jawaban menggunakan 'Ans: A' atau 'Ans: A,B,C'.")
