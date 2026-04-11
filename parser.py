import re
from docx import Document
from utils import wrap_arabic, clean_line

def parse_docx_to_moodle(docx_file):
    """
    FILE: parser.py
    LOGIKA KETAT: Hanya memproses soal yang memiliki label 'ANS'.
    """
    try:
        doc = Document(docx_file)
    except Exception as e:
        return None, {}, [], f"Error membaca file: {str(e)}"

    raw_lines = [clean_line(p.text) for p in doc.paragraphs if p.text.strip()]
    
    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen terlalu pendek atau tidak valid."

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

        # --- 1. DETEKSI TRANSISI MODE ---
        if "MULTIPLE CHOICE SET" in line_up:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; continue
        elif "MULTIPLE CHOICE" in line_up:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in line_up or "URAIAN" in line_up:
            current_mode = "ESSAY"
            i += 1; continue

        # --- 2. PROSES DATA: PILIHAN GANDA ---
        if current_mode != "ESSAY":
            if not line_up.startswith("ANS") and len(line) > 5:
                soal_text = line
                options = []
                ans_key = ""
                found_ans_for_this_q = False # Flag kelengkapan
                i += 1
                
                while i < len(raw_lines):
                    curr = raw_lines[i]
                    curr_up = curr.upper()
                    if any(m in curr_up for m in ["MULTIPLE CHOICE", "ESSAY", "URAIAN"]): break
                    
                    if curr_up.startswith("ANS"):
                        ans_key = ",".join(re.findall(r'[A-D]', curr_up))
                        found_ans_for_this_q = True
                        i += 1; break
                    
                    if len(options) < 6: options.append(curr)
                    else: soal_text += "<br/>" + curr
                    i += 1
                
                # HANYA GENERATE JIKA ADA ANS
                if found_ans_for_this_q and options and ans_key:
                    is_single = "SET" not in current_mode
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {q_num_internal:02d}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                    xml_output += f'    <single>{"true" if is_single else "false"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    for idx, opt in enumerate(options):
                        lbl = chr(65 + idx)
                        frac = ("100" if lbl in ans_key else "0") if is_single else (str(round(100/len(ans_key.split(",")), 5)) if lbl in ans_key.split(",") else "0")
                        xml_output += f'    <answer fraction="{frac}" format="html"><text><![CDATA[{wrap_arabic(opt)}]]></text></answer>\n'
                    xml_output += '  </question>\n'
                    stats[current_mode] += 1
                    q_num_internal += 1
                else:
                    audit_log.append(f"⚠️ PG Diabaikan: Tidak ada label 'ANS' atau opsi tidak lengkap.")
                continue
            else: i += 1

        # --- 3. PROSES DATA: ESSAY (WAJIB ANS) ---
        else:
            essay_combined_text = ""
            found_ans_for_essay = False
            
            # Mulai scan konten di bawah header ESSAY
            while i < len(raw_lines):
                curr_line = raw_lines[i]
                curr_up = curr_line.upper()
                
                if curr_up.startswith("ANS"):
                    found_ans_for_essay = True
                    i += 1
                    break
                
                if any(m in curr_up for m in ["MULTIPLE CHOICE"]): break
                
                essay_combined_text += curr_line + "<br/>"
                i += 1
            
            # HANYA GENERATE JIKA ADA ANS
            if found_ans_for_essay and essay_combined_text.strip():
                xml_output += f'  <question type="essay">\n'
                xml_output += f'    <name><text>Soal Essay</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_combined_text)}</p>]]></text></questiontext>\n'
                xml_output += '    <defaultgrade>1.0000000</defaultgrade>\n'
                xml_output += '    <responseformat>editor</responseformat>\n'
                xml_output += '  </question>\n'
                stats["ESSAY"] = 1
                audit_log.append("✅ Berhasil: 1 Blok Essay (Divalidasi dengan ANS)")
            else:
                audit_log.append("⚠️ Essay Diabaikan: Tidak ditemukan label 'ANS' di akhir blok.")
            continue

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket
