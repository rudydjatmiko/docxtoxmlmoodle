import re
from doc2python import doc2python
from utils import wrap_arabic

def parse_docx_to_moodle(docx_file):
    """
    FILE: parser.py
    LOGIKA: Menggunakan doc2python untuk menangkap teks Autonumbering (1., a., dll)
    """
    try:
        # doc2python mengubah autonumbering menjadi teks mentah (hardcoded strings)
        with doc2python(docx_file) as doc_extract:
            full_text = doc_extract.text
            # Pecah menjadi baris-baris, bersihkan spasi di ujung
            raw_lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    except Exception as e:
        return None, {}, [], f"Error membaca file: {str(e)}"

    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen tidak valid atau kosong."

    judul_paket = f"{raw_lines[0]} - {raw_lines[1]}"
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    current_mode = "MULTIPLE CHOICE"
    global_q_num = 1 
    stats = {"MULTIPLE CHOICE": 0, "MULTIPLE ANSWER": 0, "ESSAY": 0}
    audit_log = []
    
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        line_up = line.upper().strip()
        # Deteksi header mode tanpa spasi
        clean_header = re.sub(r'[^A-Z]', '', line_up)

        if "MULTIPLEANSWER" in clean_header:
            current_mode = "MULTIPLE ANSWER"
            i += 1; continue
        elif "MULTIPLECHOICE" in clean_header:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in clean_header or "URAIAN" in clean_header:
            current_mode = "ESSAY"
            i += 1; continue

        # --- 2. PROSES PILIHAN GANDA (SINGLE & MULTIPLE) ---
        if current_mode != "ESSAY":
            # Mencari angka di awal baris (baik diketik manual atau dari autonumbering)
            match_soal = re.match(r'^(\d+)[.\s)]+(.*)', line)
            
            if match_soal:
                soal_text = match_soal.group(2)
                options = []
                ans_key = ""
                found_ans = False
                i += 1
                
                while i < len(raw_lines):
                    curr = raw_lines[i]
                    curr_up = curr.upper().strip()
                    curr_clean = re.sub(r'[^A-Z]', '', curr_up)
                    
                    # Berhenti jika menabrak mode baru atau soal baru
                    if any(m in curr_clean for m in ["MULTIPLECHOICE", "MULTIPLEANSWER", "ESSAY", "URAIAN"]):
                        break
                    if re.match(r'^\d+[.\s)]+', curr): # Soal nomor berikutnya
                        break
                    
                    # Deteksi Kunci Jawaban
                    if curr_up.startswith("ANS"):
                        ans_key = ",".join(re.findall(r'[A-D]', curr_up))
                        found_ans = True
                        i += 1; break
                    
                    # Deteksi Huruf Opsi (a., b., c., d.)
                    # doc2python akan menampilkan bullet/numbering otomatis sebagai teks
                    match_opt = re.match(r'^([a-fA-F])[.\s)]+(.*)', curr)
                    if match_opt:
                        options.append(match_opt.group(2).strip())
                    else:
                        # Jika tidak ada huruf opsi, ini adalah teks tambahan (soal/pilihan yang panjang)
                        if not options:
                            soal_text += " " + curr
                        else:
                            options[-1] += " " + curr
                    i += 1
                
                if found_ans and options:
                    is_multiple = (current_mode == "MULTIPLE ANSWER")
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {global_q_num:02d}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                    xml_output += f'    <single>{"false" if is_multiple else "true"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    xml_output += f'    <answernumbering>abc</answernumbering>\n'
                    
                    for idx, opt in enumerate(options):
                        lbl = chr(65 + idx)
                        if not is_multiple:
                            frac = "100" if lbl in ans_key else "0"
                        else:
                            correct_count = len(ans_key.split(",")) if ans_key else 1
                            frac = str(round(100/correct_count, 5)) if lbl in ans_key else "0"
                        
                        xml_output += f'    <answer fraction="{frac}" format="html">\n'
                        xml_output += f'      <text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
                        xml_output += f'    </answer>\n'
                    
                    xml_output += '  </question>\n'
                    stats[current_mode] = stats.get(current_mode, 0) + 1
                    global_q_num += 1
                continue
            else: i += 1

        # --- 3. PROSES ESSAY ---
        else:
            essay_text = ""
            found_ans_essay = False
            while i < len(raw_lines):
                curr_line = raw_lines[i]
                if curr_line.upper().startswith("ANS"):
                    found_ans_essay = True
                    i += 1; break
                essay_text += curr_line + "<br/>"
                i += 1
            
            if found_ans_essay and essay_text.strip():
                xml_output += f'  <question type="essay">\n'
                xml_output += f'    <name><text>Soal {global_q_num:02d} (Essay)</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_text)}</p>]]></text></questiontext>\n'
                xml_output += '    <responseformat>editor</responseformat>\n'
                xml_output += '  </question>\n'
                stats["ESSAY"] = stats.get("ESSAY", 0) + 1
                global_q_num += 1
            continue

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket
