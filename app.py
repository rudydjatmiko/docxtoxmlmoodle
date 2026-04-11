import streamlit as st
from docx import Document
import re
import io

# --- CONFIG PAGE ---
st.set_page_config(page_title="PAI Moodle Converter", page_icon="🌙", layout="wide")

# --- FUNGSI PENDUKUNG ---
def wrap_arabic(text):
    if not text: return ""
    # Mendeteksi karakter Arab
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

def convert_docx_to_moodle_xml(docx_file):
    try:
        doc = Document(docx_file)
        # Sanitasi teks: hapus spasi kosong dan karakter non-breaking space
        raw_lines = [p.text.replace('\xa0', ' ').strip() for p in doc.paragraphs if p.text.strip()]
        
        if not raw_lines:
            return None, {}, [], "File Kosong"

        # Judul diambil dari 2 baris pertama
        judul_paket = " ".join(raw_lines[:2])
        xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
        
        current_mode = "MULTIPLE CHOICE"
        q_num_internal = 1
        stats = {"MULTIPLE CHOICE": 0, "MULTIPLE CHOICE SET": 0, "ESSAY": 0}
        audit_log = []
        
        i = 0
        while i < len(raw_lines):
            line = raw_lines[i]
            line_up = line.upper()

            # 1. DETEKSI PERUBAHAN TIPE SOAL (Poin 1 & 5)
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
            match_soal = re.match(r'^\s*(\d+)[\.\s]+(.*)', line)
            
            if match_soal and current_mode != "ESSAY":
                soal_num_doc = match_soal.group(1)
                soal_text = match_soal.group(2)
                options = []
                ans_key = ""
                i += 1
                
                # 3. DETEKSI PILIHAN JAWABAN / HURUF LEVEL 2 (Poin 3)
                while i < len(raw_lines):
                    curr_line = raw_lines[i]
                    curr_up = curr_line.upper()
                    
                    # Berhenti jika ketemu tipe soal baru di tengah jalan
                    if any(x in curr_up for x in ["MULTIPLE CHOICE", "ESSAY"]):
                        break

                    # 4. DETEKSI "ANS:" (Poin 4)
                    if curr_up.startswith("ANS:"):
                        ans_key = "".join(re.findall(r'[A-D,]', curr_up.replace("ANS:", "")))
                        if not ans_key: # Jika Ans: dan kunci beda baris
                            i += 1
                            if i < len(raw_lines):
                                ans_key = "".join(re.findall(r'[A-D,]', raw_lines[i].upper()))
                        i += 1
                        break
                    
                    # Deteksi pilihan jawaban (a. b. c. d.)
                    match_opt = re.match(r'^\s*([a-dA-D])[\.\)\-\s]+(.*)', curr_line)
                    if match_opt:
                        options.append(match_opt.group(2).strip())
                    elif not re.match(r'^\s*\d+[\.\s]+', curr_line):
                        soal_text += " " + curr_line
                    else:
                        break
                    i += 1
                
                # GENERASI XML JIKA VALID
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
                            corrects = [x.strip() for x in ans_key.split(',')]
                            fraction = str(round(100/len(corrects), 5)) if lbl in corrects else "0"
                        else:
                            fraction = "100" if lbl == ans_key else "0"
                        
                        xml_output += f'    <answer fraction="{fraction}" format="html">\n'
                        xml_output += f'      <text><![CDATA[{wrap_arabic(opt_text)}]]></text>\n'
                        xml_output += f'    </answer>\n'
                    
                    xml_output += '  </question>\n'
                    stats[current_mode] += 1
                    audit_log.append(f"✅ Soal {soal_num_doc}: Berhasil")
                    q_num_internal += 1
                continue

            elif current_mode == "ESSAY":
                essay_text = "<br/>".join(raw_lines[i:])
                essay_text = re.sub(r'Ans:.*', '', essay_text, flags=re.IGNORECASE | re.DOTALL)
                xml_output += f'  <question type="essay">\n    <name><text>Soal {q_num_internal:02d} (Essay)</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_text)}</p>]]></text></questiontext>\n'
                xml_output += '    <responseformat>editor</responseformat><responserequired>1</responserequired>\n  </question>\n'
                stats["ESSAY"] += 1
                audit_log.append(f"✅ Bagian Essay Berhasil")
                break
            else:
                i += 1

        xml_output += '</quiz>'
        return xml_output, stats, audit_log, judul_paket
    except Exception as e:
        return None, {}, [], str(e)

# --- ANTARMUKA STREAMLIT ---
st.title("🌙 Moodle XML Hierarchical Converter")
st.markdown("---")

file = st.file_uploader("Upload SAT PAI (Format .docx)", type=["docx"])

if file:
    xml_data, statistik, logs, info = convert_docx_to_moodle_xml(file)
    
    if xml_data:
        st.success(f"📌 Judul: {info}")
        
        # Dashboard Statistik
        total_soal = sum(statistik.values())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PG Biasa", statistik.get("MULTIPLE CHOICE", 0))
        c2.metric("PG Set", statistik.get("MULTIPLE CHOICE SET", 0))
        c3.metric("Essay", statistik.get("ESSAY", 0))
        c4.metric("TOTAL", total_soal)
        
        # Download Section
        st.download_button(
            label="📥 Download XML Moodle",
            data=xml_data,
            file_name=file.name.replace(".docx", ".xml"),
            mime="text/xml",
            use_container_width=True
        )
        
        # Log Audit
        with st.expander("🔍 Lihat Log Deteksi Per Nomor"):
            for log in logs:
                st.write(log)
    else:
        st.error(f"Terjadi kesalahan saat membaca file: {info}")
