import streamlit as st
from docx import Document
import re
import io

# --- FUNGSI PENDUKUNG ---
def wrap_arabic(text):
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

# --- FUNGSI KONVERSI HIERARKI ---
def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    raw_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    # State Management
    current_mode = "MULTIPLE CHOICE"
    q_num_internal = 1
    stats = {"MULTIPLE CHOICE": 0, "MULTIPLE CHOICE SET": 0, "ESSAY": 0}
    audit_log = []
    
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        line_up = line.upper()

        # 1. DETEKSI TIPE SOAL (Poin 1 & 5)
        if "MULTIPLE CHOICE SET" in line_up:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; continue
        elif "MULTIPLE CHOICE" in line_up:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in line_up:
            current_mode = "ESSAY"
            i += 1; continue

        # 2. DETEKSI NOMOR SOAL / ANGKA LEVEL 1 (Poin 2)
        match_soal = re.match(r'^(\d+)[.\s]+(.*)', line)
        
        if match_soal and current_mode != "ESSAY":
            soal_num_doc = match_soal.group(1)
            soal_text = match_soal.group(2)
            options = []
            ans_key = ""
            i += 1
            
            # 3. DETEKSI PILIHAN JAWABAN / HURUF LEVEL 2 (Poin 3)
            while i < len(raw_lines):
                curr_line = raw_lines[i]
                
                # 4. DETEKSI "ANS:" SEBAGAI AKHIR SOAL (Poin 4)
                if curr_line.upper().startswith("ANS:"):
                    ans_key = "".join(re.findall(r'[A-D,]', curr_line.upper()))
                    i += 1
                    break
                
                # Cek apakah ini pilihan jawaban (a. b. c. d.)
                match_opt = re.match(r'^[a-dA-D][.\)\-\s]+(.*)', curr_line)
                if match_opt:
                    options.append(match_opt.group(1).strip())
                elif not re.match(r'^\d+[.\s]+', curr_line):
                    # Jika bukan angka/nomor soal baru, maka ini teks lanjutan soal
                    soal_text += " " + curr_line
                else:
                    # Jika ketemu angka (Level 1) tanpa ada ANS, berarti soal sebelumnya cacat
                    break
                i += 1
            
            # GENERASI XML JIKA VALID
            if options and ans_key:
                is_single = "SET" not in current_mode
                xml_output += f'  <question type="multichoice">\n'
                xml_output += f'    <name><text>Soal {q_num_internal:02d} (Dokumen No {soal_num_doc})</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                xml_output += f'    <single>{"true" if is_single else "false"}</single>\n'
                xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                xml_output += f'    <answernumbering>abc</answernumbering>\n'

                labels = ["A", "B", "C", "D"]
                for idx, opt_text in enumerate(options[:4]):
                    lbl = labels[idx]
                    if not is_single:
                        corrects = [x.strip() for x in ans_key.split(',')]
                        fraction = str(round(100/len(corrects), 5)) if lbl in corrects else "0"
                    else:
                        fraction = "100" if lbl == ans_key else "0"
                    
                    xml_output += f'    <answer fraction="{fraction}" format="html">\n'
                    xml_output += f'      <text><![CDATA[{wrap_arabic(opt_text)}]]></text>\n'
                    xml_output += f'    </answer>\n'
                
                xml_output += '  </question>\n'
                stats[current_mode] += 1
                audit_log.append(f"✅ Berhasil: Soal {soal_num_doc} ({current_mode})")
                q_num_internal += 1
            else:
                audit_log.append(f"❌ Gagal: Soal {soal_num_doc} (Cek format Opsi/Ans)")
            continue

        elif current_mode == "ESSAY":
            essay_text = "<br/>".join(raw_lines[i:])
            essay_text = re.sub(r'Ans:.*', '', essay_text, flags=re.IGNORECASE)
            xml_output += f'  <question type="essay">\n    <name><text>Soal {q_num_internal:02d} (Essay)</text></name>\n'
            xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_text)}</p>]]></text></questiontext>\n'
            xml_output += '    <responseformat>editor</responseformat><responserequired>1</responserequired>\n  </question>\n'
            stats["ESSAY"] += 1
            audit_log.append(f"✅ Berhasil: Bagian Essay")
            break
        else:
            i += 1

    xml_output += '</quiz>'
    return xml_output, stats, audit_log

# --- UI STREAMLIT ---
st.set_page_config(page_title="Moodle Hierarki Fixer", page_icon="🎯")
st.title("🎯 Moodle Converter Berbasis Hierarki")

file = st.file_uploader("Upload SAT9 AkidAH 9.docx", type=["docx"])

if file:
    xml_final, statistik, logs = convert_docx_to_moodle_xml(file)
    
    # DASHBOARD STATISTIK
    st.subheader("📊 Statistik Jumlah Soal Terbaca")
    total_soal = sum(statistik.values())
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PG Biasa", statistik["MULTIPLE CHOICE"])
    col2.metric("PG Kompleks", statistik["MULTIPLE CHOICE SET"])
    col3.metric("Essay", statistik["ESSAY"])
    col4.metric("TOTAL SOAL", total_soal)

    if total_soal < 26:
        st.error(f"⚠️ Perhatian: Hanya {total_soal} soal terdeteksi. Harusnya 26.")
    else:
        st.success(f"🎉 Sempurna! Semua {total_soal} soal berhasil terbaca.")

    with st.expander("🔍 Detail Audit Soal (Cek Nomor yang Hilang)"):
        for log in logs:
            st.write(log)

    st.download_button("📥 Download XML Final", xml_final, "Akidah_Moodle_Fixed.xml", "text/xml", use_container_width=True)
