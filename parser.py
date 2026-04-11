import re
from docx import Document
from utils import wrap_arabic, clean_line

def parse_docx_to_moodle(docx_file):
    """
    FILE: parser.py
    FIX: Mendukung header tanpa spasi (MULTIPLECHOICE, MULTIPLEANSWER, ESSAY).
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
    global_q_num = 1 
    stats = {"MULTIPLE CHOICE": 0, "MULTIPLE ANSWER": 0, "ESSAY": 0}
    audit_log = []
    
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        # Membersihkan spasi untuk pengecekan header
        line_check = line.upper().replace(" ", "").strip()

        # --- 1. DETEKSI TRANSISI MODE (SENSITIF TANPA SPASI) ---
        if "MULTIPLEANSWER" in line_check:
            current_mode = "MULTIPLE ANSWER"
            i += 1; continue
        elif "MULTIPLECHOICE" in line_check:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in line_check or "URAIAN" in line_check:
            current_mode = "ESSAY"
            i += 1; continue

        # --- 2. PROSES DATA: PILIHAN GANDA ---
        if current_mode != "ESSAY":
            if not line_check.startswith("ANS") and len(line) > 5:
                soal_text = line
                options = []
                ans_key = ""
                found_ans = False
                i += 1
                
                while i < len(raw_lines):
                    curr = raw_lines[i]
                    curr_check = curr.upper().replace(" ", "").strip()
                    
                    # Stop jika bertemu header mode apa pun (tanpa spasi)
                    if any(m in curr_check for m in ["MULTIPLECHOICE", "MULTIPLEANSWER", "ESSAY", "URAIAN"]):
                        break
                    
                    if curr_check.startswith("ANS"):
                        ans_key = ",".join(re.findall(r'[A-D]', curr_check))
                        found_ans = True
                        i += 1; break
                    
                    if len(options) < 6:
                        options.append(curr)
                    else:
                        soal_text += "<br/>" + curr
                    i += 1
                
                if found_ans and options and ans_key:
                    is_multiple = (current_mode == "MULTIPLE ANSWER")
                    correct_labels = [x.strip() for x in ans_key.split(",")]
                    
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {global_q_num:02d}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                    xml_output += f'    <single>{"false" if is_multiple else "true"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    
                    for idx, opt in enumerate(options):
                        lbl = chr(65 + idx)
                        if not is_multiple:
                            frac = "100" if lbl in correct_labels else "0"
                        else:
                            frac = str(round(100/len(correct_labels), 5)) if lbl in correct_labels else "0"
                        
                        xml_output += f'    <answer fraction="{frac}" format="html">\n'
                        xml_output += f'      <text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
                        xml_output += f'    </answer>\n'
                    
                    xml_output += '  </question>\n'
                    stats[current_mode] = stats.get(current_mode, 0) + 1
                    global_q_num += 1
                continue
            else: i += 1

        # --- 3. PROSES DATA: ESSAY ---
        else:
            essay_text = ""
            found_ans_essay = False
            while i < len(raw_lines):
                curr_line = raw_lines[i]
                curr_check = curr_line.upper().replace(" ", "").strip()
                
                if curr_check.startswith("ANS"):
                    found_ans_essay = True
                    i += 1; break
                
                if "MULTIPLE" in curr_check: break
                
                essay_text += curr_line + "<br/>"
                i += 1
            
            if found_ans_essay and essay_text.strip():
                xml_output += f'  <question type="essay">\n'
                xml_output += f'    <name><text>Soal {global_q_num:02d}</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_text)}</p>]]></text></questiontext>\n'
                xml_output += '    <responseformat>editor</responseformat>\n'
                xml_output += '  </question>\n'
                stats["ESSAY"] = stats.get("ESSAY", 0) + 1
                global_q_num += 1
            continue

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket
