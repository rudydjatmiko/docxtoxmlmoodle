import streamlit as st
from docx import Document
import re

# --- FUNGSI PENDUKUNG ---
def wrap_arabic(text):
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    raw_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    if not raw_lines:
        return None, {}, [], "File Kosong"

    judul_paket = raw_lines[0]
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    # State Management
    current_mode = "MULTIPLE CHOICE"
    q_num_internal = 1
    stats = {"MULTIPLE CHOICE": 0, "MULTIPLE CHOICE SET": 0, "ESSAY": 0}
    audit_log = []
    
    i = 1
    while i < len(raw_lines):
        line = raw_lines[i]
        line_up = line.upper()

        # 1. Deteksi Tipe Soal (Penanda Header)
        if "MULTIPLE CHOICE SET" in line_up:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; continue
        elif "MULTIPLE CHOICE" in line_up:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in line_up:
            current_mode = "ESSAY"
            i += 1; continue

        # 2. Deteksi Nomor Soal (Level 1 - Angka)
        match_soal = re.match(r'^(\d+)[.\s]+(.*)', line)
        
        if match_soal and current_mode != "ESSAY":
            soal_num_doc = match_soal.group(1)
            soal_text = match_soal.group(2)
            options = []
            ans_key = ""
            i += 1
            
            # 3 & 4. Deteksi Pilihan (Level 2 - Huruf) & ANS
            while i < len(raw_lines):
                curr_line = raw_lines[i]
                curr_up = curr_line.upper()
                
                if curr_up.startswith("ANS:"):
                    # Ambil kunci (bisa single 'A' atau set 'A,B,D')
                    ans_key = "".join(re.findall(r'[A-D,]', curr_up))
                    i += 1
                    break
                
                # Cek baris pilihan (a. b. c. d.)
                match_opt = re.match(r'^[a-dA-D][.\)\-\s]+(.*)', curr_line)
                if match_opt:
                    options.append(match_opt.group(1).strip())
                elif not re.match(r'^\d+[.\s]+', curr_line) and not any(m in curr_up for m in ["MULTIPLE CHOICE", "ESSAY"]):
                    soal_text += " " + curr_line
                else:
                    break
                i += 1
            
            # Buat XML Question
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
                audit_log.append(f"✅ No {soal_num_doc}: Berhasil")
                q_num_internal += 1
            continue

        elif current_mode == "ESSAY":
            essay_block = "<br/>".join(raw_lines[i:])
            essay_block = re.sub(r'Ans:.*', '', essay_block, flags=re.IGNORECASE)
            xml_output += f'  <question type="essay">\n    <name><text>Soal {q_num_internal:02d} (Essay)</text></name>\n'
            xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_block)}</p>]]></text></questiontext>\n'
            xml_output += '    <responseformat>editor</responseformat><responserequired>1</responserequired>\n  </question>\n'
            stats["ESSAY"] += 1
            audit_log.append(f"✅ Bagian Essay Berhasil")
            break
        else:
            i += 1

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="PAI Moodle Converter", page_icon="🌙")
st.title("🌙 PAI Moodle XML Converter")

uploaded_file = st.file_uploader("Upload File Docx Soal", type=["docx"])

if uploaded_file:
    with st.spinner('Memproses dokumen...'):
        xml_result, statistik, log_audit, judul = convert_docx_to_moodle_xml(uploaded_file)
    
    if xml_result:
        st.info(f"📋 **Paket Soal:** {judul}")
        
        # Dashboard Metrik
        st.subheader("📊 Statistik Soal")
        total = sum(statistik.values())
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("PG Biasa", statistik.get("MULTIPLE CHOICE", 0))
        m2.metric("PG Set", statistik.get("MULTIPLE CHOICE SET", 0))
        m3.metric("Essay", statistik.get("ESSAY", 0))
        m4.metric("Total", total)

        # Download
        st.download_button(
            label="📥 Download XML untuk Moodle",
            data=xml_result,
            file_name=f"{judul.replace(' ', '_')}.xml",
            mime="text/xml",
            use_container_width=True
        )

        with st.expander("🔍 Lihat Log Audit"):
            for log in log_audit:
                st.write(log)
