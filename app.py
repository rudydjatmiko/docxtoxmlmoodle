import streamlit as st
from docx import Document
import re
import io

# --- FUNGSI PENDUKUNG ---
def wrap_arabic(text):
    if not text: return ""
    # Deteksi teks Arab untuk styling RTL
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

def convert_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    # Ambil semua baris teks yang tidak kosong
    raw_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    i = 0
    q_num = 1
    
    while i < len(raw_lines):
        line = raw_lines[i]

        # 1. Abaikan Header/Judul
        if any(x in line.upper() for x in ["SAT PAI", "AKIDAH", "MULTIPLE CHOICE"]):
            if "SET" not in line.upper(): # Jangan abaikan penanda MULTIPLE CHOICE SET
                i += 1
                continue

        # 2. PROSES ESSAY
        if line.upper() == "ESSAY" or "KERJAKAN SOAL BERIKUT" in line.upper():
            i += 1
            essay_text = "<br/>".join(raw_lines[i:])
            xml_output += f"""
  <question type="essay">
    <name><text>Soal {q_num:02d} (Essay)</text></name>
    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_text)}</p>]]></text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
    <responsefieldlines>15</responsefieldlines>
  </question>\n"""
            break

        # 3. PROSES PILIHAN GANDA (LOGIKA BACKWARD TRACKING)
        if not line.upper().startswith("ANS:"):
            # Kumpulkan baris sampai ketemu "Ans:"
            temp_block = []
            while i < len(raw_lines) and not raw_lines[i].upper().startswith("ANS:"):
                # Abaikan penanda tipe soal di tengah-tengah
                if raw_lines[i].upper() not in ["MULTIPLE CHOICE", "MULTIPLE CHOICE SET"]:
                    temp_block.append(raw_lines[i])
                i += 1
            
            # Jika berhenti karena ketemu "Ans:"
            if i < len(raw_lines) and raw_lines[i].upper().startswith("ANS:"):
                ans_key = raw_lines[i].upper().replace("ANS:", "").strip()
                i += 1
                
                # Sesuai file Anda: 4 baris terakhir di blok adalah pilihan A, B, C, D
                if len(temp_block) >= 5:
                    choices = temp_block[-4:] # 4 baris terakhir
                    question_parts = temp_block[:-4] # sisanya adalah soal
                    question_text = "<br/>".join([wrap_arabic(p) for p in question_parts])
                    
                    # Deteksi tipe (Single atau Multi)
                    is_mcs = "," in ans_key
                    q_type = "multichoice" # Moodle menggunakan type multichoice untuk keduanya
                    
                    xml_output += f'  <question type="{q_type}">\n'
                    xml_output += f'    <name><text>Soal {q_num:02d}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{question_text}</p>]]></text></questiontext>\n'
                    xml_output += f'    <single>{"false" if is_mcs else "true"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    xml_output += f'    <answernumbering>abc</answernumbering>\n'

                    # Mapping label ke index (A=0, B=1, C=2, D=3)
                    labels = ["A", "B", "C", "D"]
                    for idx, c_text in enumerate(choices):
                        current_label = labels[idx]
                        
                        # Hitung Skor
                        if is_mcs:
                            correct_list = [x.strip() for x in ans_key.split(',')]
                            # Bobot dibagi rata (misal 3 jawaban benar = 33.33%)
                            fraction = str(100 / len(correct_list)) if current_label in correct_list else "0"
                        else:
                            fraction = "100" if current_label == ans_key else "0"
                        
                        xml_output += f'    <answer fraction="{fraction}" format="html">\n'
                        xml_output += f'      <text><![CDATA[{wrap_arabic(c_text)}]]></text>\n'
                        xml_output += f'    </answer>\n'
                    
                    xml_output += '  </question>\n'
                    q_num += 1
            else:
                i += 1
        else:
            i += 1

    xml_output += '</quiz>'
    return xml_output

# --- ANTARMUKA STREAMLIT ---
st.set_page_config(page_title="Moodle XML Final Fix", page_icon="✅")
st.title("✅ Moodle XML Converter (Final Version)")
st.write("Skrip ini sudah diperbaiki untuk memisahkan Soal dan Pilihan secara otomatis.")

uploaded_file = st.file_uploader("Upload file SAT9 AkidAH 9.docx", type=["docx"])

if uploaded_file:
    try:
        xml_result = convert_to_moodle_xml(uploaded_file)
        
        # Berikan preview kecil
        st.success("Konversi Berhasil!")
        
        # Tombol Download
        file_name = uploaded_file.name.replace(".docx", ".xml")
        st.download_button(
            label="📥 Download File XML untuk Moodle",
            data=xml_result,
            file_name=file_name,
            mime="text/xml"
        )
        
        with st.expander("Lihat Preview XML"):
            st.code(xml_result[:1000] + "...", language='xml')
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
