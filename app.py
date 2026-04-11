import streamlit as st
from docx import Document
import re
import io

def wrap_arabic(text):
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    # Ambil baris non-kosong
    raw_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    current_mode = "MULTIPLE CHOICE" 
    q_num = 1
    i = 0
    
    stats = {"PG (Single)": 0, "PG Kompleks (Set)": 0, "Essay": 0}
    debug_list = [] # Untuk melacak soal yang terbaca

    while i < len(raw_lines):
        line = raw_lines[i]
        line_upper = line.upper()

        # 1. DETEKSI PERUBAHAN MODE
        if "MULTIPLE CHOICE SET" in line_upper:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1
            continue
        elif "MULTIPLE CHOICE" in line_upper:
            current_mode = "MULTIPLE CHOICE"
            i += 1
            continue
        elif "ESSAY" in line_upper:
            current_mode = "ESSAY"
            i += 1
            continue
        
        # Abaikan header dokumen
        if any(h in line_upper for h in ["SAT PAI", "AKIDAH", "TAHUN PELAJARAN"]):
            i += 1
            continue

        # 2. PROSES SOAL
        if current_mode == "ESSAY":
            # Mode Essay: Cari semua teks sampai akhir
            essay_content = "<br/>".join(raw_lines[i:])
            # Bersihkan Ans: --- jika ada
            essay_content = re.sub(r'Ans:.*', '', essay_content, flags=re.IGNORECASE)
            
            xml_output += f"""
  <question type="essay">
    <name><text>Soal {q_num:02d} (Essay)</text></name>
    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_content)}</p>]]></text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
    <responsefieldlines>15</responsefieldlines>
  </question>\n"""
            stats["Essay"] += 1
            debug_list.append(f"Soal {q_num}: [ESSAY] {essay_content[:50]}...")
            break 

        else:
            block = []
            while i < len(raw_lines):
                curr = raw_lines[i]
                curr_up = curr.upper()
                if curr_up.startswith("ANS:") or any(m in curr_up for m in ["MULTIPLE CHOICE", "ESSAY"]):
                    break
                block.append(curr)
                i += 1
            
            if i < len(raw_lines) and raw_lines[i].upper().startswith("ANS:"):
                ans_key = raw_lines[i].upper().replace("ANS:", "").strip()
                i += 1
                
                # Sesuai pola: 4 baris terakhir dalam blok adalah pilihan
                if len(block) >= 5:
                    choices = block[-4:] 
                    question_body = block[:-4] 
                    q_text_plain = " ".join(question_body)
                    q_html = "".join([f"<p>{wrap_arabic(p)}</p>" for p in question_body])
                    
                    is_single = "SET" not in current_mode
                    
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {q_num:02d}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[{q_html}]]></text></questiontext>\n'
                    xml_output += f'    <single>{"true" if is_single else "false"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    xml_output += f'    <answernumbering>abc</answernumbering>\n'

                    labels = ["A", "B", "C", "D"]
                    for idx, c_text in enumerate(choices):
                        label = labels[idx]
                        if not is_single:
                            correct_list = [x.strip() for x in ans_key.split(',')]
                            fraction = str(round(100/len(correct_list), 5)) if label in correct_list else "0"
                        else:
                            fraction = "100" if label == ans_key else "0"
                        
                        xml_output += f'    <answer fraction="{fraction}" format="html">\n'
                        xml_output += f'      <text><![CDATA[{wrap_arabic(c_text)}]]></text>\n'
                        xml_output += f'    </answer>\n'
                    
                    xml_output += '  </question>\n'
                    
                    if is_single: stats["PG (Single)"] += 1
                    else: stats["PG Kompleks (Set)"] += 1
                    debug_list.append(f"Soal {q_num}: [{current_mode}] {q_text_plain[:50]}...")
                    q_num += 1
            else:
                i += 1

    xml_output += '</quiz>'
    return xml_output, stats, debug_list

# --- UI STREAMLIT ---
st.set_page_config(page_title="Fixer Moodle 26 Soal", page_icon="🎯")
st.title("🎯 Moodle Converter (Audit Mode)")

uploaded = st.file_uploader("Upload .docx", type=["docx"])

if uploaded:
    xml_data, stats, debug = convert_docx_to_moodle_xml(uploaded)
    
    # 1. Dashboard Statistik
    st.subheader("📊 Statistik Deteksi")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Single", stats["PG (Single)"])
    c2.metric("Set", stats["PG Kompleks (Set)"])
    c3.metric("Essay", stats["Essay"])
    total = sum(stats.values())
    c4.metric("TOTAL", total)

    if total < 26:
        st.warning(f"Terdeteksi {total} soal. Jika seharusnya 26, periksa apakah ada soal yang tidak memiliki baris 'Ans:' atau pilihan jawabannya kurang dari 4 baris.")

    # 2. Daftar Audit (Cek soal mana yang terbaca)
    with st.expander("🔍 Lihat Daftar Soal yang Terbaca"):
        for d in debug:
            st.write(d)

    # 3. Tombol Download
    st.download_button("📥 Download XML", xml_data, "soal_akidah_fix.xml", "text/xml", use_container_width=True)
