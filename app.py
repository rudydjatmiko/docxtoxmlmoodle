import streamlit as st
from docx import Document
import re
import html

# Fungsi untuk membungkus teks Arab dengan style 30px
def wrap_arabic(text):
    if not text: return ""
    # Range unicode untuk karakter Arab
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 30px; line-height: 1.8;">\1</span>', text)

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    # Ambil semua teks baris per baris, abaikan baris kosong
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    xml_footer = '</quiz>'
    questions_xml = ""
    
    q_num = 1
    i = 0
    while i < len(lines):
        line = lines[i]

        # 1. DETEKSI SOAL ESSAY (SOAL TERAKHIR / NOMOR 26)
        if "Berdasarkan kisah Sultan" in line or "Tuliskan terjemahan" in line:
            # Ambil semua sisa baris sebagai isi soal essay
            essay_content = "<br/>".join(lines[i:])
            essay_content = wrap_arabic(essay_content)
            questions_xml += f"""
  <question type="essay">
    <name><text>Soal {q_num} (Essay)</text></name>
    <questiontext format="html">
      <text><![CDATA[<p>{essay_content}</p>]]></text>
    </questiontext>
    <defaultgrade>50</defaultgrade>
    <responseformat>editor</responseformat>
    <responsefieldlines>25</responsefieldlines>
  </question>\n"""
            break # Hentikan loop karena essay biasanya di akhir

        # 2. DETEKSI PILIHAN GANDA (1-22) & MULTIPLE CHOICE SET (23-25)
        # Kita asumsikan baris baru yang bukan "Ans:" dan bukan pilihan adalah SOAL
        if not line.startswith("Ans:") and not re.match(r'^[A-E][\.:\)]', line):
            q_text = wrap_arabic(line)
            # Tentukan tipe berdasarkan nomor soal
            q_type = "multichoiceset" if 23 <= q_num <= 25 else "multichoice"
            
            current_q_xml = f'  <question type="{q_type}">\n'
            current_q_xml += f'    <name><text>Soal {q_num}</text></name>\n'
            current_q_xml += f'    <questiontext format="html">\n      <text><![CDATA[<p>{q_text}</p>]]></text>\n    </questiontext>\n'
            
            i += 1
            choices = []
            ans_key = ""
            
            # Ambil baris-baris di bawah soal sampai ketemu "Ans:"
            while i < len(lines):
                if lines[i].startswith("Ans:"):
                    ans_key = lines[i].replace("Ans:", "").strip()
                    i += 1
                    break
                else:
                    choices.append(lines[i])
                    i += 1
            
            # Proses Pilihan Jawaban
            for idx, choice_text in enumerate(choices):
                # Bersihkan prefix A. B. C. jika ada
                clean_choice = re.sub(r'^[A-E][\.:\)]\s*', '', choice_text)
                clean_choice = wrap_arabic(clean_choice)
                
                # Cek apakah ini jawaban benar
                # (Untuk MCS, ans_key bisa berisi "A,B" atau "AB")
                label = chr(65 + idx) # A, B, C...
                fraction = "100" if label in ans_key else "0"
                if q_type == "multichoiceset" and label in ans_key:
                    # Pada MCS, jika ada 2 benar, masing-masing beri 50 atau sesuai logika All-or-Nothing
                    # Namun di plugin All-or-Nothing, biasanya tetap 100/benar
                    fraction = "100" 
                
                current_q_xml += f'    <answer fraction="{fraction}" format="html">\n      <text><![CDATA[{clean_choice}]]></text>\n    </answer>\n'
            
            current_q_xml += '    <single>true</single>\n' if q_type == "multichoice" else '    <single>false</single>\n'
            current_q_xml += '  </question>\n'
            questions_xml += current_q_xml
            q_num += 1
        else:
            i += 1
            
    return xml_header + questions_xml + xml_footer

# Tampilan Streamlit
st.title("🕌 Konverter Word ke Moodle (Quran Arab)")
st.info("Pastikan format soal di Word: Soal -> Pilihan A-D -> Ans: Kunci")

file = st.file_uploader("Upload File .docx", type=["docx"])

if file:
    hasil_xml = convert_docx_to_moodle_xml(file)
    st.success("Konversi Selesai!")
    st.download_button("Download XML Moodle", hasil_xml, file_name="soal_moodle.xml", mime="text/xml")
