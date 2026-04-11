import streamlit as st
from docx import Document
import re
import base64

# --- 1. FUNGSI PENDUKUNG (BACKEND) ---

def wrap_arabic(text):
    """Mendeteksi teks Arab dan memberikan styling font besar."""
    if not text: return ""
    # Pattern untuk mendeteksi karakter Arabic
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

def is_choice_pattern(text):
    """Mendeteksi apakah baris diawali label pilihan A-E secara manual."""
    # Pola: A. atau A) atau A: di awal baris
    return re.match(r'^[A-E][\.:\)]\s+', text.strip())

# --- 2. FUNGSI INTI KONVERSI ---

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    all_images = get_images_from_docx(doc)
    # Ambil semua paragraf, simpan string kosong untuk baris kosong antar paragraf soal
    raw_lines = [p.text.strip() for p in doc.paragraphs]
    
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    questions_xml = ""
    stats = {"PG": 0, "MCS": 0, "Essay": 0, "Gambar": 0}
    
    q_num = 1
    img_idx = 0 
    i = 0
    
    while i < len(raw_lines):
        line = raw_lines[i]
        if not line: # Lewati baris kosong di awal atau antar soal
            i += 1
            continue

        # A. DETEKSI ESSAY
        if line.upper() == "ESSAY" or "KERJAKAN SOAL BERIKUT" in line.upper():
            if line.upper() == "ESSAY": i += 1
            # Gabungkan sisa semua baris sebagai satu atau lebih soal essay
            essay_content = wrap_arabic("<br/>".join([l for l in raw_lines[i:] if l]))
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

        # B. DETEKSI SOAL BERPARAGRAF (PG / MULTIPLE RESPONSE)
        if not line.upper().startswith("ANS:") and not line.isupper():
            q_parts = [line]
            i += 1
            choices = []
            ans_key = ""
            
            # Kumpulkan semua baris teks sampai bertemu pilihan jawaban atau kunci jawaban
            while i < len(raw_lines):
                curr = raw_lines[i]
                if not curr: 
                    i += 1
                    continue
                
                if curr.upper().startswith("ANS:"):
                    ans_key = curr.upper().replace("ANS:", "").strip()
                    i += 1
                    break
                elif is_choice_pattern(curr):
                    # Mulai fase pengumpulan pilihan jawaban
                    choices.append(re.sub(r'^[A-E][\.:\)]\s+', '', curr))
                    i += 1
                    # Kumpulkan pilihan berikutnya atau sambungan pilihan
                    while i < len(raw_lines):
                        next_curr = raw_lines[i]
                        if not next_curr: 
                            i += 1
                            continue
                        if next_curr.upper().startswith("ANS:"):
                            break
                        elif is_choice_pattern(next_curr):
                            choices.append(re.sub(r'^[A-E][\.:\)]\s+', '', next_curr))
                        else:
                            # Jika teks biasa di bawah pilihan, gabungkan ke pilihan terakhir
                            if choices: choices[-1] += f" <br/> {next_curr}"
                        i += 1
                else:
                    # Jika belum ketemu pola pilihan, ini adalah paragraf lanjutan soal
                    q_parts.append(curr)
                    i += 1
            
            # Gabungkan paragraf soal dengan tag <p> agar rapi
            q_full_text = "".join([f"<p>{wrap_arabic(p)}</p>" for p in q_parts])
            
            # Deteksi Placeholder Gambar
            img_tag = ""
            file_tag = ""
            if re.search(r'\[(Image|GAMBAR|RUMUS)\]', q_full_text, re.IGNORECASE) and img_idx < len(all_images):
                img_data = all_images[img_idx]
                img_name = f"img_{q_num}.png"
                img_tag = f'<p><img src="@@PLUGINFILE@@/{img_name}"/></p>'
                file_tag = f'<file name="{img_name}" path="/" encoding="base64">{img_data}</file>'
                img_idx += 1
                stats["Gambar"] += 1
                q_full_text = re.sub(r'\[(Image|GAMBAR|RUMUS)\]', '', q_full_text, flags=re.IGNORECASE)

            # Logika Deteksi Tipe Soal (Otomatis)
            is_mcs = "," in ans_key or "PILIH" in q_full_text.upper()
            q_type = "multichoiceset" if is_mcs else "multichoice"
            
            if is_mcs: stats["MCS"] += 1
            else: stats["PG"] += 1
            
            # Bangun XML Per Soal
            current_q = f'  <question type="{q_type}">\n'
            current_q += f'    <name><text>Soal {q_num:02d}</text></name>\n'
            current_q += f'    <questiontext format="html">\n      <text><![CDATA[{q_full_text}{img_tag}]]></text>\n      {file_tag}\n    </questiontext>\n'
            current_q += f'    <single>{"false" if is_mcs else "true"}</single>\n    <shuffleanswers>true</shuffleanswers>\n    <answernumbering>abc</answernumbering>\n'
            
            for idx, c_text in enumerate(choices):
                label = chr(65 + idx)
                if is_mcs:
                    correct_list = [x.strip() for x in ans_key.split(',')]
                    # Bobot nilai dibagi rata untuk jawaban benar
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

# --- 3. TAMPILAN ANTARMUKA (STREAMLIT) ---

st.set_page_config(page_title="Moodle Converter Pro", page_icon="🕋")

st.title("🕋 Moodle XML Converter Pro")
st.markdown("Konversi soal Word ke XML Moodle dengan dukungan **Paragraf**, **Gambar**, dan **Teks Arab**.")

uploaded_file = st.file_uploader("Upload file soal .docx", type=["docx"])

if uploaded_file:
    # Nama file dinamis mengikuti file asli
    nama_xml = re.sub(r'\.docx$', '.xml', uploaded_file.name, flags=re.IGNORECASE)
    if not nama_xml.endswith('.xml'): nama_xml += '.xml'

    with st.spinner('Menganalisis file...'):
        try:
            hasil_xml, statistik = convert_docx_to_moodle_xml(uploaded_file)
            
            st.success(f"Berhasil memproses: {uploaded_file.name}")
            
            # Dashboard Statistik Konfirmasi
            st.subheader("📊 Ringkasan Konversi")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Soal", statistik["PG"] + statistik["MCS"] + statistik["Essay"])
            col2.metric("Pilihan Ganda", statistik["PG"])
            col3.metric("Multi-Response", statistik["MCS"])
            col4.metric("Essay", statistik["Essay"])
            
            if statistik["Gambar"] > 0:
                st.info(f"🖼️ Terdeteksi {statistik['Gambar']} gambar/rumus.")

            st.divider()

            # Tombol Download dengan Lebar Penuh
            st.download_button(
                label=f"📥 DOWNLOAD {nama_xml.upper()}", 
                data=hasil_xml, 
                file_name=nama_xml, 
                mime="text/xml",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"Gagal mengonversi: {e}")

st.caption("Gunakan format 'Ans: A' atau 'Ans: A,B,C' di akhir soal.")
