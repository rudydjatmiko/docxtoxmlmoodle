import streamlit as st
from docx import Document
import re
import base64

# --- 1. FUNGSI PENDUKUNG ---

def wrap_arabic(text):
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 30px; line-height: 1.8;">\1</span>', text)

def is_choice(text):
    """Mendeteksi apakah baris adalah pilihan jawaban (A. teks, B. teks, dll)"""
    return re.match(r'^[A-E][\.:\)]\s*', text.strip())

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    # Ambil baris yang benar-benar berisi teks
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    questions_xml = ""
    stats = {"PG": 0, "MCS": 0, "Essay": 0}
    
    q_num = 1
    i = 0
    
    while i < len(lines):
        line = lines[i]

        # Abaikan header atau baris instruksi umum
        if line.upper() in ["MULTIPLE CHOICE", "MULTIPLE CHOICE SET", "AKIDAH", "SAT PAI 2025-2026"]:
            i += 1
            continue

        # A. DETEKSI ESSAY
        if line.upper() == "ESSAY" or "KERJAKAN SOAL BERIKUT" in line.upper():
            i += 1
            essay_content = "<br/>".join(lines[i:])
            questions_xml += f"""
  <question type="essay">
    <name><text>Soal {q_num:02d} (Essay)</text></name>
    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_content)}</p>]]></text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
    <responsefieldlines>15</responsefieldlines>
  </question>\n"""
            stats["Essay"] += 1
            break 

        # B. PROSES SOAL DAN PILIHAN
        if not line.upper().startswith("ANS:"):
            q_text_parts = [line]
            i += 1
            choices = []
            ans_key = ""
            
            # 1. Kumpulkan teks soal (bisa lebih dari 1 paragraf)
            while i < len(lines) and not is_choice(lines[i]) and not lines[i].upper().startswith("ANS:"):
                q_parts_upper = lines[i].upper()
                if q_parts_upper in ["MULTIPLE CHOICE", "MULTIPLE CHOICE SET"]:
                    i += 1
                    continue
                q_text_parts.append(lines[i])
                i += 1
            
            # 2. Kumpulkan Pilihan Jawaban
            while i < len(lines) and not lines[i].upper().startswith("ANS:"):
                if is_choice(lines[i]):
                    clean_choice = re.sub(r'^[A-E][\.:\)]\s*', '', lines[i])
                    choices.append(clean_choice)
                i += 1
            
            # 3. Ambil Kunci Jawaban
            if i < len(lines) and lines[i].upper().startswith("ANS:"):
                ans_key = lines[i].upper().replace("ANS:", "").strip()
                i += 1

            # --- LOGIKA PENENTU TIPE SOAL ---
            # HANYA dianggap Multiple Choice Set (MCS) jika kunci jawaban punya KOMA (A,B,C)
            is_mcs = "," in ans_key
            q_type = "multichoiceset" if is_mcs else "multichoice"
            
            if is_mcs: stats["MCS"] += 1
            else: stats["PG"] += 1

            # Gabungkan teks soal dengan paragraf rapi
            q_html = "".join([f"<p>{wrap_arabic(t)}</p>" for t in q_text_parts])

            # Bangun XML
            current_q = f'  <question type="{q_type}">\n'
            current_q += f'    <name><text>Soal {q_num:02d}</text></name>\n'
            current_q += f'    <questiontext format="html"><text><![CDATA[{q_html}]]></text></questiontext>\n'
            current_q += f'    <single>{"false" if is_mcs else "true"}</single>\n'
            current_q += f'    <shuffleanswers>true</shuffleanswers>\n'
            current_q += f'    <answernumbering>abc</answernumbering>\n'
            
            for idx, c_text in enumerate(choices):
                label = chr(65 + idx)
                if is_mcs:
                    correct_list = [x.strip() for x in ans_key.split(',')]
                    fraction = str(100 // len(correct_list)) if label in correct_list else "0"
                else:
                    fraction = "100" if label == ans_key else "0"
                
                current_q += f'    <answer fraction="{fraction}" format="html">\n      <text><![CDATA[{wrap_arabic(c_text)}]]></text>\n    </answer>\n'
            
            current_q += '  </question>\n'
            questions_xml += current_q
            q_num += 1
        else:
            i += 1
            
    return xml_header + questions_xml + '</quiz>', stats

# --- UI STREAMLIT ---
st.set_page_config(page_title="Moodle Fixer", page_icon="✅")
st.title("✅ Moodle XML Fixer (Akurasi Tinggi)")
uploaded_file = st.file_uploader("Upload file .docx", type=["docx"])

if uploaded_file:
    nama_xml = re.sub(r'\.docx$', '.xml', uploaded_file.name, flags=re.IGNORECASE)
    hasil_xml, statistik = convert_docx_to_moodle_xml(uploaded_file)
    
    st.subheader("📊 Hasil Deteksi")
    col1, col2, col3 = st.columns(3)
    col1.metric("Pilihan Ganda", statistik["PG"])
    col2.metric("Multi-Response", statistik["MCS"])
    col3.metric("Essay", statistik["Essay"])
    
    st.download_button(f"📥 DOWNLOAD {nama_xml.upper()}", data=hasil_xml, file_name=nama_xml, mime="text/xml")
