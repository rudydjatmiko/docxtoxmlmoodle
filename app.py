import streamlit as st
from docx import Document
import re
import io

# --- CONFIG ---
st.set_page_config(page_title="Moodle Converter Final Fix", layout="wide")

def wrap_arabic(text):
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    # Sanitasi: Ambil teks dan bersihkan spasi aneh
    raw_lines = [p.text.replace('\xa0', ' ').strip() for p in doc.paragraphs if p.text.strip()]
    
    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen terlalu pendek atau kosong."

    judul_paket = f"{raw_lines[0]} - {raw_lines[1]}"
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    # State Awal: Paksa harus PG dulu
    current_mode = "MULTIPLE CHOICE"
    q_num_internal = 1
    stats = {"MULTIPLE CHOICE": 0, "MULTIPLE CHOICE SET": 0, "ESSAY": 0}
    audit_log = []
    
    i = 0
    # Lewati baris judul sampai ketemu kata kunci MULTIPLE CHOICE atau angka 1.
    while i < len(raw_lines):
        txt = raw_lines[i].upper()
        if "MULTIPLE CHOICE SET" in txt:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; break
        elif "MULTIPLE CHOICE" in txt:
            current_mode = "MULTIPLE CHOICE"
            i += 1; break
        elif re.match(r'^\d+[.\s]+', txt): # Jika langsung ketemu angka 1
            break
        i += 1

    # Loop Utama
    while i < len(raw_lines):
        line = raw_lines[i]
        line_up = line.upper()

        # 1. CEK PERUBAHAN MODE
        if "MULTIPLE CHOICE SET" in line_up:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; continue
        elif "ESSAY" in line_up or "URAIAN" in line_up:
            current_mode = "ESSAY"
            i += 1; # Jangan continue, langsung proses sisa sebagai essay
        
        if current_mode == "ESSAY":
            essay_block = "<br/>".join(raw_lines[i:])
            essay_block = re.sub(r'Ans:.*', '', essay_block, flags=re.IGNORECASE | re.DOTALL)
            xml_output += f'  <question type="essay">\n    <name><text>Soal {q_num_internal:02d} (Essay)</text></name>\n'
            xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_block)}</p>]]></text></questiontext>\n'
            xml_output += '    <responseformat>editor</responseformat><responserequired>1</responserequired>\n  </question>\n'
            stats["ESSAY"] += 1
            audit_log.append("✅ Bagian Essay Berhasil")
            break

        # 2. DETEKSI NOMOR SOAL (LEVEL 1)
        match_soal = re.match(r'^(\d+)[.\s]+(.*)', line)
        if match_soal:
            soal_num_doc = match_soal.group(1)
            soal_text = match_soal.group(2)
            options = []
            ans_key = ""
            i += 1
            
            # 3. DETEKSI OPSI (LEVEL 2) & ANS
            while i < len(raw_lines):
                curr_line = raw_lines[i]
                curr_up = curr_line.upper()
                
                # Jika ketemu pembatas tipe soal baru
                if any(m in curr_up for m in ["MULTIPLE CHOICE", "ESSAY", "URAIAN"]):
                    break
                
                # Deteksi ANS:
                if curr_up.startswith("ANS"):
                    ans_key = "".join(re.findall(r'[A-D,]', curr_up.replace("ANS", "")))
                    if not ans_key and i+1 < len(raw_lines):
                        ans_key = "".join(re.findall(r'[A-D,]', raw_lines[i+1].upper()))
                        i += 1
                    i += 1
                    break
                
                # Deteksi Huruf Opsi (a. b. c. d.)
                match_opt = re.match(r'^[a-dA-D][.\)\-\s]+(.*)', curr_line)
                if match_opt:
                    options.append(match_opt.group(1).strip())
                elif not re.match(r'^\d+[.\s]+', curr_line):
                    soal_text += " " + curr_line
                else:
                    break # Ketemu angka baru
                i += 1
            
            # GENERASI XML
            if options and ans_key:
                is_single = "SET" not in current_mode
                xml_output += f'  <question type="multichoice">\n'
                xml_output += f'    <name><text>Soal {q_num_internal:02d} (No {soal_num_doc})</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                xml_output += f'    <single>{"true" if is_single else "false"}</single>\n'
                xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                xml_output += f'    <answer fraction="{"100" if is_single else "0"}" format="html">\n' # Fallback
                
                labels = ["A", "B", "C", "D"]
                xml_temp = ""
                for idx, opt_text in enumerate(options[:4]):
                    lbl = labels[idx]
                    if not is_single:
                        corrects = [x.strip() for x in ans_key.split(',')]
                        fraction = str(round(100/len(corrects), 5)) if lbl in corrects else "0"
                    else:
                        fraction = "100" if lbl == ans_key else "0"
                    
                    xml_temp += f'    <answer fraction="{fraction}" format="html">\n'
                    xml_temp += f'      <text><![CDATA[{wrap_arabic(opt_text)}]]></text>\n'
                    xml_temp += f'    </answer>\n'
                
                xml_output += xml_temp + '  </question>\n'
                stats[current_mode] += 1
                audit_log.append(f"✅ Soal {soal_num_doc} Berhasil")
                q_num_internal += 1
            else:
                audit_log.append(f"❌ Soal {soal_num_doc} Gagal (Cek format Opsi/Ans)")
        else:
            i += 1

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket

# --- UI ---
st.title("🌙 Moodle Converter (Fixed Hierarchical)")
f = st.file_uploader("Upload Docx", type=["docx"])
if f:
    xml, res, logs, jdl = convert_docx_to_moodle_xml(f)
    if xml:
        st.success(f"Berhasil Membaca: {jdl}")
        st.write("### Statistik Soal Terbaca:")
        st.write(res)
        st.download_button("📥 Download XML", xml, file_name="moodle_final.xml")
        with st.expander("Log Audit"):
            for l in logs: st.write(l)
