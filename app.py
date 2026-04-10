import streamlit as st
from docx import Document
import re
import base64
import io

# 1. Fungsi untuk membungkus teks Arab agar besar dan rapi di Moodle
def wrap_arabic(text):
    if not text: return ""
    # Pattern untuk mendeteksi karakter Arabic Unicode
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    # Menggunakan font Traditional Arabic 30px sesuai standar soal keagamaan
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 30px; line-height: 1.8;">\1</span>', text)

# 2. Fungsi ekstraksi gambar (mendukung gambar biasa & persamaan yang dianggap gambar)
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

# 3. Fungsi Utama Konversi mengikuti standar ekspor XML Moodle yang Anda kirim
def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    all_images = get_images_from_docx(doc)
    
    # Ambil teks paragraf, bersihkan spasi kosong
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    # Header XML Moodle Standar
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    questions_xml = ""
    
    q_num = 1
    img_counter = 0 
    i = 0
    
    while i < len(lines):
        line = lines[i]

        # --- A. DETEKSI SOAL ESSAY ---
        # Berdasarkan pola file Anda (soal di bawah kata ESSAY atau kata kunci tertentu)
        if "Berdasarkan kisah" in line or "Tuliskan terjemahan" in line or line.upper() == "ESSAY":
            if line.upper() == "ESSAY": i += 1 # Lewati baris bertuliskan "ESSAY"
            
            # Ambil semua baris sisa sebagai satu atau beberapa soal essay
            essay_content = wrap_arabic("<br/>".join(lines[i:]))
            questions_xml += f"""
  <question type="essay">
    <name><text>Soal {q_num:02d} (Essay)</text></name>
    <questiontext format="html">
      <text><![CDATA[<p>{essay_content}</p>]]></text>
    </questiontext>
    <generalfeedback format="html"><text></text></generalfeedback>
    <defaultgrade>1.0000000</defaultgrade>
    <penalty>0.3333333</penalty>
    <hidden>0</hidden>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
    <responsefieldlines>15</responsefieldlines>
    <attachments>0</attachments>
  </question>\n"""
            break 

        # --- B. DETEKSI PILIHAN GANDA (PG) ---
        # Abaikan baris header seperti "MULTIPLE CHOICE", "QURDIS", dll
        if not line.startswith("Ans:") and not line.isupper():
            q_text = wrap_arabic(line)
            
            # Logika Gambar: Sisipkan jika ada placeholder [Image], [GAMBAR], atau [RUMUS]
            img_tag = ""
            file_tag = ""
            if re.search(r'\[(Image|GAMBAR|RUMUS)\]', line, re.IGNORECASE) and img_counter < len(all_images):
                img_data = all_images[img_counter]
                img_name = f"img_{q_num}_{img_counter}.png"
                img_tag = f'<p><img src="@@PLUGINFILE@@/{img_name}" alt="visual"/></p>'
                file_tag = f'<file name="{img_name}" path="/" encoding="base64">{img_data}</file>'
                img_counter += 1
                # Hapus placeholder dari teks agar bersih
                q_text = re.sub(r'\[(Image|GAMBAR|RUMUS)\]', '', q_text, flags=re.IGNORECASE).strip()

            i += 1
            choices = []
            ans_key = "A" # Default kunci jika tidak ditemukan
            
            # Ambil pilihan jawaban (baris-baris di bawah soal sampai ketemu "Ans:")
            while i < len(lines):
                if lines[i].upper().startswith("ANS:"):
                    ans_key = lines[i].replace("Ans:", "").replace("ANS:", "").strip().upper()
                    i += 1
                    break
                else:
                    # Bersihkan label manual (A., B., dst) agar tidak dobel jika guru mengetik manual
                    clean_choice = re.sub(r'^[A-E][\.:\)]\s*', '', lines[i])
                    choices.append(clean_choice)
                    i += 1
            
            # Tentukan tipe (Multi Choice Set untuk nomor 23-25 sesuai instruksi Anda sebelumnya)
            q_type = "multichoiceset" if 23 <= q_num <= 25 else "multichoice"
            
            current_q_xml = f'  <question type="{q_type}">\n'
            current_q_xml += f'    <name><text>Soal {q_num:02d}</text></name>\n'
            current_q_xml += f'    <questiontext format="html">\n'
            current_q_xml += f'      <text><![CDATA[<p>{q_text}</p>{img_tag}]]></text>\n'
            if file_tag: current_q_xml += f'      {file_tag}\n'
            current_q_xml += f'    </questiontext>\n'
            current_q_xml += f'    <defaultgrade>1.0000000</defaultgrade>\n'
            current_q_xml += f'    <single>{"true" if q_type=="multichoice" else "false"}</single>\n'
            current_q_xml += f'    <shuffleanswers>true</shuffleanswers>\n'
            current_q_xml += f'    <answernumbering>abc</answernumbering>\n'
            
            # Generate Pilihan Jawaban (A, B, C, D otomatis)
            for idx, choice_text in enumerate(choices):
                label = chr(65 + idx) # 65 adalah 'A'
                fraction = "100" if label in ans_key else "0"
                
                current_q_xml += f'    <answer fraction="{fraction}" format="html">\n'
                current_q_xml += f'      <text><![CDATA[{wrap_arabic(choice_text)}]]></text>\n'
                current_q_xml += f'      <feedback><text></text></feedback>\n'
                current_q_xml += f'    </answer>\n'
            
            current_q_xml += '  </question>\n'
            questions_xml += current_q_xml
            q_num += 1
        else:
            i += 1
            
    return xml_header + questions_xml + '</quiz>'

# --- TAMPILAN STREAMLIT (UI) ---
st.set_page_config(page_title="Moodle Converter Pro", page_icon="📝")

st.title("📝 Moodle XML Converter Pro")
st.markdown("""
Aplikasi ini mengonversi file Word (.docx) ke format XML Moodle yang siap impor.
**Fitur Utama:**
- Mendukung **Teks Arab** (Otomatis diperbesar).
- Mendukung **Gambar & Persamaan Matematika** (Gunakan penanda `[GAMBAR]` di Word).
- **Auto-Fix Label:** Memberi label A, B, C, D otomatis meskipun tidak diketik di Word.
- Penomoran rapi **2 Digit** (Soal 01, Soal 02).
""")

uploaded_file = st.file_uploader("Pilih file soal .docx", type=["docx"])

if uploaded_file:
    with st.spinner('Sedang memproses...'):
        try:
            hasil_xml = convert_docx_to_moodle_xml(uploaded_file)
            st.success("Konversi Berhasil!")
            st.download_button(
                label="📥 Download XML Moodle", 
                data=hasil_xml, 
                file_name="soal_moodle_pro.xml", 
                mime="text/xml"
            )
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")

st.divider()
st.caption("Pastikan format kunci jawaban adalah 'Ans: A' di bawah pilihan terakhir.")
