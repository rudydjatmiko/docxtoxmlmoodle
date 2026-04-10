import streamlit as st
from docx import Document
import re
import base64
import io

# Fungsi untuk membungkus teks Arab dengan style 30px
def wrap_arabic(text):
    if not text: return ""
    # Range unicode untuk karakter Arab
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 30px; line-height: 1.8;">\1</span>', text)

def get_images_from_docx(doc):
    """Mengekstrak gambar dari dokumen Word dan menyimpannya dalam dictionary."""
    images = []
    # Mengakses blok relasi dokumen untuk mengambil data gambar
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            img_data = rel.target_part.blob
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            images.append(img_base64)
    return images

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    # Ambil semua gambar yang ada di file Word
    all_images = get_images_from_docx(doc)
    
    # Ambil semua teks baris per baris
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    xml_footer = '</quiz>'
    questions_xml = ""
    
    q_num = 1
    img_counter = 0 # Penanda urutan gambar yang ditemukan
    i = 0
    
    while i < len(lines):
        line = lines[i]

        # 1. DETEKSI SOAL ESSAY (SOAL TERAKHIR / NOMOR 26)
        if "Berdasarkan kisah Sultan" in line or "Tuliskan terjemahan" in line:
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
            break 

        # 2. DETEKSI PILIHAN GANDA & MULTIPLE CHOICE SET
        if not line.startswith("Ans:") and not re.match(r'^[A-E][\.:\)]', line):
            q_text = wrap_arabic(line)
            q_type = "multichoiceset" if 23 <= q_num <= 25 else "multichoice"
            
            # Cek jika soal ini kemungkinan memiliki gambar (asumsi gambar muncul berurutan)
            # Di Moodle, gambar dimasukkan via tag <img> dan data Base64 dimasukkan di tag <file>
            img_tag = ""
            file_tag = ""
            
            # Logika sederhana: Jika di dokumen Word ada gambar, kita coba pasangkan ke soal
            # Tips: Jika soal tertentu ada gambar, tuliskan [GAMBAR] di Word agar lebih akurat
            if "[GAMBAR]" in line.upper() and img_counter < len(all_images):
                img_data = all_images[img_counter]
                img_filename = f"gambar_{q_num}.png"
                img_tag = f'<p><img src="@@PLUGINFILE@@/{img_filename}" alt="gambar" /></p>'
                file_tag = f'<file name="{img_filename}" path="/" encoding="base64">{img_data}</file>'
                img_counter += 1
                # Hapus teks penanda [GAMBAR] agar tidak muncul di soal
                q_text = re.sub(r'\[GAMBAR\]', '', q_text, flags=re.IGNORECASE)

            current_q_xml = f'  <question type="{q_type}">\n'
            current_q_xml += f'    <name><text>Soal {q_num}</text></name>\n'
            current_q_xml += f'    <questiontext format="html">\n'
            current_q_xml += f'      <text><![CDATA[<p>{q_text}</p>{img_tag}]]></text>\n'
            if file_tag:
                current_q_xml += f'      {file_tag}\n'
            current_q_xml += f'    </questiontext>\n'
            
            i += 1
            choices = []
            ans_key = ""
            
            while i < len(lines):
                if lines[i].startswith("Ans:"):
                    ans_key = lines[i].replace("Ans:", "").strip()
                    i += 1
                    break
                else:
                    choices.append(lines[i])
                    i += 1
            
            for idx, choice_text in enumerate(choices):
                clean_choice = re.sub(r'^[A-E][\.:\)]\s*', '', choice_text)
                clean_choice = wrap_arabic(clean_choice)
                label = chr(65 + idx)
                fraction = "100" if label in ans_key else "0"
                
                current_q_xml += f'    <answer fraction="{fraction}" format="html">\n      <text><![CDATA[{clean_choice}]]></text>\n    </answer>\n'
            
            current_q_xml += '    <single>true</single>\n' if q_type == "multichoice" else '    <single>false</single>\n'
            current_q_xml += '  </question>\n'
            questions_xml += current_q_xml
            q_num += 1
        else:
            i += 1
            
    return xml_header + questions_xml + xml_footer

# --- Tampilan Streamlit ---
st.set_page_config(page_title="Konverter Moodle", page_icon="🕌")
st.title("🕌 Konverter Word ke Moodle (Support Gambar)")
st.markdown("""
### Cara Penggunaan:
1. Pastikan setiap soal ditulis dalam format yang benar. type soal yang berlaku: multiple choice, multiple choice set, dan essay
2. Tulis "Ans: [Kunci]" di diakhir soal.
3. **Penting:** Jika soal memiliki gambar, ketik teks `[GAMBAR]` di dalam kalimat soalnya agar sistem tahu di mana harus meletakkan gambar tersebut.
""")

file = st.file_uploader("Upload File .docx", type=["docx"])

if file:
    with st.spinner('Sedang mengonversi...'):
        try:
            hasil_xml = convert_docx_to_moodle_xml(file)
            st.success("Konversi Selesai!")
            st.download_button(
                label="📥 Download XML Moodle", 
                data=hasil_xml, 
                file_name="soal_moodle_bergambar.xml", 
                mime="text/xml"
            )
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
