import streamlit as st
from docx import Document
import re
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Moodle XML Final Converter", page_icon="🌙", layout="wide")

def wrap_arabic(text):
    """Membungkus teks Arab dengan styling RTL agar tampil rapi di Moodle."""
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    # Sanitasi: Bersihkan karakter non-breaking space (\xa0) dan spasi berlebih
    raw_lines = [p.text.replace('\xa0', ' ').strip() for p in doc.paragraphs if p.text.strip()]
    
    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen terlalu pendek atau kosong."

    # Mengambil judul dari dua baris pertama dokumen [cite: 1, 2]
    judul_paket = f"{raw_lines[0]} - {raw_lines[1]}"
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    current_mode = "MULTIPLE CHOICE"
    q_num_internal = 1
    stats = {"MULTIPLE CHOICE": 0, "MULTIPLE CHOICE SET": 0, "ESSAY": 0}
    audit_log = []
    
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        line_up = line.upper()

        # 1. DETEKSI PERUBAHAN MODE
        if "MULTIPLE CHOICE SET" in line_up:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; continue
        elif "MULTIPLE CHOICE" in line_up:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in line_up or "URAIAN" in line_up:
            current_mode = "ESSAY"
            i += 1; continue

        # 2. LOGIKA PILIHAN GANDA (SINGLE & SET)
        if current_mode != "ESSAY":
            # Mencari pola angka di awal baris (contoh: 1. atau 20.) [cite: 4, 131]
            match_soal = re.match(r'^(\d+)[.\s]+(.*)', line)
            if match_soal:
                soal_num_doc = match_soal.group(1)
                soal_text = match_soal.group(2)
                options = []
                ans_key = ""
                i += 1
                
                # Mengumpulkan opsi, teks tambahan, dan kunci jawaban
                while i < len(raw_lines):
                    curr_line = raw_lines[i]
                    curr_up = curr_line.upper()
                    
                    # Berhenti jika menabrak penanda mode baru
                    if any(m in curr_up for m in ["MULTIPLE CHOICE", "ESSAY", "URAIAN"]):
                        break
                    
                    # Deteksi Kunci Jawaban (Ans:) [cite: 9, 165]
                    if curr_up.startswith("ANS"):
                        ans_key = "".join(re.findall(r'[A-D,]', curr_up.replace("ANS", "")))
                        # Jika kunci di baris bawahnya
                        if not ans_key and i+1 < len(raw_lines):
                            ans_key = "".join(re.findall(r'[A-D,]', raw_lines[i+1].upper()))
                            i += 1
                        i += 1
                        break
                    
                    # Deteksi Opsi Jawaban (a. b. c. d.) [cite: 5, 161]
                    match_opt = re.match(r'^[a-dA-D][.\)\-\s]+(.*)', curr_line)
                    if match_opt:
                        options.append(match_opt.group(1).strip())
                    elif not re.match(r'^\d+[.\s]+', curr_line):
                        # Jika teks bukan angka baru, berarti lanjutan narasi soal [cite: 72-76]
                        soal_text += "<br/>" + curr_line
                    else:
                        break # Ketemu nomor soal berikutnya
                    i += 1
                
                # Konstruksi XML untuk Pilihan Ganda
                if options and ans_key:
                    is_single = "SET" not in current_mode
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {q_num_internal:02d} (No {soal_num_doc})</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                    xml_output += f'    <single>{"true" if is_single else "false"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    xml_output += f'    <answernumbering>abc</answernumbering>\n'
                    
                    labels = ["A", "B", "C", "D"]
                    for idx, opt_text in enumerate(options[:4]):
                        lbl = labels[idx]
                        if not is_single:
                            # Pembagian bobot untuk soal Pilihan Ganda Kompleks [cite: 160-164]
                            corrects = [x.strip() for x in ans_key.split(',')]
                            fraction = str(round(100/len(corrects), 5)) if lbl in corrects else "0"
                        else:
                            fraction = "100" if lbl == ans_key else "0"
                        
                        xml_output += f'    <answer fraction="{fraction}" format="html">\n'
                        xml_output += f'      <text><![CDATA[{wrap_arabic(opt_text)}]]></text>\n'
                        xml_output += f'    </answer>\n'
                    
                    xml_output += '  </question>\n'
                    stats[current_mode] += 1
                    audit_log.append(f"✅ Berhasil: Soal PG No {soal_num_doc}")
                    q_num_internal += 1
                else:
                    audit_log.append(f"❌ Gagal: Soal PG No {soal_num_doc} (Opsi/Kunci tidak lengkap)")
                continue
            else:
                i += 1
        
        # 3. LOGIKA ESSAY (Memecah butir soal per nomor) 
        else:
            match_essay = re.match(r'^(\d+)[.\s]+(.*)', line)
            if match_essay:
                essay_num = match_essay.group(1)
                essay_text = match_essay.group(2)
                i += 1
                
                # Mengambil baris tambahan di bawah teks soal essay
                while i < len(raw_lines):
                    if re.match(r'^\d+[.\s]+', raw_lines[i]) or "ANS" in raw_lines[i].upper():
                        break
                    essay_text += "<br/>" + raw_lines[i]
                    i += 1
                
                xml_output += f'  <question type="essay">\n'
                xml_output += f'    <name><text>Soal {q_num_internal:02d} (Essay {essay_num})</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_text)}</p>]]></text></questiontext>\n'
                xml_output += '    <responseformat>editor</responseformat><responserequired>1</responserequired>\n'
                xml_output += '  </question>\n'
                stats["ESSAY"] += 1
                audit_log.append(f"✅ Berhasil: Soal Essay No {essay_num}")
                q_num_internal += 1
            else:
                i += 1

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket

# --- ANTARMUKA (UI) ---
st.title("🌙 Moodle XML Ultimate Converter")
st.markdown("---")

uploaded_file = st.file_uploader("Upload File Docx (SAT PAI/Akidah)", type=["docx"])

if uploaded_file:
    with st.spinner("Sedang memproses dokumen..."):
        xml_data, statistik, logs, info = convert_docx_to_moodle_xml(uploaded_file)
    
    if xml_data:
        st.success(f"📌 File Terdeteksi: **{info}**")
        
        # Dashboard Statistik
        total_soal = sum(statistik.values())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PG Biasa", statistik.get("MULTIPLE CHOICE", 0))
        c2.metric("PG Kompleks (SET)", statistik.get("MULTIPLE CHOICE SET", 0))
        c3.metric("Essay", statistik.get("ESSAY", 0))
        c4.metric("TOTAL SOAL", total_soal)
        
        # Tombol Download
        st.download_button(
            label="📥 Download XML Moodle",
            data=xml_data,
            file_name=f"Moodle_Ready_{uploaded_file.name.replace('.docx', '.xml')}",
            mime="text/xml",
            use_container_width=True
        )
        
        # Log Detail
        with st.expander("🔍 Lihat Log Audit Pemrosesan"):
            for entry in logs:
                st.write(entry)
    else:
        st.error(f"Gagal memproses file: {info}")
