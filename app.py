import streamlit as st
from docx import Document
import re
import base64
import io

# --- 1. FUNGSI BACKEND (PEMROSESAN TEKS) ---

def wrap_arabic(text):
    """Memberikan styling RTL dan font besar khusus teks Arab."""
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 30px; line-height: 1.8;">\1</span>', text)

def get_images_from_docx(doc):
    """Mengekstrak semua gambar dari file Word."""
    images = []
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            try:
                img_data = rel.target_part.blob
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                images.append(img_base64)
            except: continue
    return images

def is_choice_label(text):
    """Deteksi jika baris diawali label A., B., C), dll."""
    return re.match(r'^[A-E][\.:\)]\s*', text.strip())

# --- 2. LOGIKA UTAMA KONVERSI ---

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    all_images = get_images_from_docx(doc)
    # Ambil baris teks yang bersih
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    questions_xml = ""
    stats = {"PG": 0, "MCS": 0, "Essay": 0, "Gambar": 0}
    
    q_num = 1
    img_idx = 0 
    i = 0
    
    while i < len(lines):
        line = lines[i]

        # A. FILTER HEADER (Abaikan teks judul)
        if line.upper() in ["MULTIPLE CHOICE", "MULTIPLE CHOICE SET", "AKIDAH", "QURDIS"]:
            i += 1
            continue

        # B. DETEKSI ESSAY
        if line.upper() == "ESSAY" or "KERJAKAN SOAL BERIKUT" in line.upper():
            i += 1
            essay_body = "<br/>".join(lines[i:])
            questions_xml += f"""
  <question type="essay">
    <name><text>Soal {q_num:02d} (Essay)</text></name>
    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_body)}</p>]]></text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
    <responsefieldlines>15</responsefieldlines>
  </question>\n"""
            stats["Essay"] += 1
            break 

        # C. DETEKSI SOAL PILIHAN (PG / MULTI)
        if not line.upper().startswith("ANS:"):
            q_text_parts = [line]
            i += 1
            choices = []
            ans_key = ""
            
            # 1. Kumpulkan teks soal (mendukung baris baru/paragraf)
            while i < len(lines) and not is_choice_label(lines[i]) and not lines[i].upper().startswith("ANS:"):
                # Jika baris bukan pilihan tapi ada di bawah soal, anggap paragraf soal
                q_text_parts.append(lines[i])
                i += 1
            
            # 2. Kumpulkan Pilihan Jawaban
            while i < len(lines) and not lines[i].upper().startswith("ANS:"):
                # Jika diawali A. B. C. maka ambil sebagai pilihan baru
                if is_choice_label(lines[i]):
                    clean_c = re.sub(r'^[A-E][\.:\)]\s*', '', lines[i])
                    choices.append(clean_c)
                # Jika tidak diawali A-E tapi kita sudah dalam mode "mengumpul pilihan", gabungkan ke pilihan terakhir
                elif choices:
                    choices[-1] += f" <br/> {lines[i]}"
                i += 1
            
            # 3. Ambil Kunci Jawaban
            if i < len(lines) and lines[i].upper().startswith("ANS:"):
                ans_key = lines[i].upper().replace("ANS:", "").strip()
                i += 1

            # Tentukan Tipe Soal (Hanya MCS jika kunci pakai koma)
            is_mcs = "," in ans_key
            q_type = "multichoiceset" if is_mcs else "multichoice"
            
            if is_mcs: stats["MCS"] += 1
            else: stats["PG"] += 1

            # Olah Gambar (Jika ada placeholder [Image X] atau [GAMBAR])
            img_html = ""
            img_file_xml = ""
            q_full_text = "".join([f"<p>{wrap_arabic(t)}</p>" for t in q_text_parts])
            
            if re.search(r'\[(Image|GAMBAR)\]', q_full_text, re.IGNORECASE) and img_idx < len(all_images):
                img_name = f"img_{q_num}.png"
                img_html = f'<p><img src="@@PLUGINFILE@@/{img_name}"/></p>'
                img_file_xml = f'<file name="{img_name}" path="/" encoding="base64">{all_images[img_idx]}</file>'
                img_idx += 1
                stats["Gambar"] += 1
                q_full_text = re.sub(r'\[(Image|GAMBAR)\]', '', q_full_text, flags=re.IGNORECASE)

            # Bangun Struktur XML
            current_q = f'  <question type="{q_type}">\n'
            current_q += f'    <name><text>Soal {q_num:02d}</text></name>\n'
            current_q += f'    <questiontext format="html">\n      <text><![CDATA[{q_full_text}{img_html}]]></text>\n      {img_file_xml}\n    </questiontext>\n'
            current_q += f'    <single>{"false" if is_mcs else "true"}</single>\n    <shuffleanswers>true</shuffleanswers>\n    <answernumbering>abc</answernumbering>\n'
            
            # Masukkan pilihan jawaban ke tag <answer>
            for idx, c_text in enumerate(choices):
                label = chr(65 + idx)
                if is_mcs:
                    corrects = [x.strip() for x in ans_key.split(',')]
                    fraction = str(100 // len(corrects)) if label in corrects else "0"
                else:
                    fraction = "100" if label == ans_key else "0"
                
                current_q += f'    <answer fraction="{fraction}" format="html">\n      <text><![CDATA[{wrap_arabic(c_text)}]]></text>\n    </answer>\n'
            
            current_q += '  </question>\n'
            questions_xml += current_q
            q_num += 1
        else:
            i += 1
            
    return xml_header + questions_xml + '</quiz>', stats

# --- 3. ANTARMUKA (UI) STREAMLIT ---

st.set_page_config(page_title="Moodle Converter Final", page_icon="🎯")
st.title("🎯 Moodle XML Converter Final")
st.info("Unggah file .docx. Pastikan kunci jawaban ditulis 'Ans: A' atau 'Ans: A,B'.")

uploaded_file = st.file_uploader("Pilih file Word", type=["docx"])

if uploaded_file:
    nama_file = uploaded_file.name.rsplit('.', 1)[0] + ".xml"
    
    with st.spinner('Sedang mengonversi...'):
        try:
            hasil_xml, statistik = convert_docx_to_moodle_xml(uploaded_file)
            
            st.success("✅ Konversi Selesai!")
            
            # Dashboard Hasil
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Pilihan Ganda", statistik["PG"])
            c2.metric("Multi-Respons", statistik["MCS"])
            c3.metric("Essay", statistik["Essay"])
            c4.metric("Gambar", statistik["Gambar"])
            
            st.download_button(
                label=f"📥 DOWNLOAD {nama_file.upper()}",
                data=hasil_xml,
                file_name=nama_file,
                mime="text/xml",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption("Versi Final 1.0 - Optimal untuk Soal Agama & Bahasa Indonesia.")
