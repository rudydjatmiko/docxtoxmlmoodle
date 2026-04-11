import re
from docx import Document
from utils import wrap_arabic, clean_line

def parse_docx_to_moodle(docx_file):
    """
    FILE: parser.py
    LOGIKA: Dioptimalkan untuk format SAT PAI (Penomoran Kontinu & Toleransi Spasi).
    """
    try:
        doc = Document(docx_file)
    except Exception as e:
        return None, {}, [], f"Error membaca file: {str(e)}"

    # Ambil baris, bersihkan spasi aneh, abaikan baris yang benar-benar kosong
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
        line_up = line.upper().strip()
        # Bersihkan karakter non-huruf untuk deteksi header mode
        clean_header = re.sub(r'[^A-Z]', '', line_up)

        # --- 1. DETEKSI TRANSISI MODE ---
        if "MULTIPLEANSWER" in clean_header:
            current_mode = "MULTIPLE ANSWER"
            i += 1; continue
        elif "MULTIPLECHOICE" in clean_header:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in clean_header or "URAIAN" in clean_header:
            current_mode = "ESSAY"
            i += 1; continue

        # --- 2. PROSES DATA: PILIHAN GANDA (SINGLE & MULTIPLE) ---
        if current_mode != "ESSAY":
            # Jika baris diawali angka (1. atau 10.), ambil teks setelahnya sebagai awal soal
            match_soal = re.match(r'^\d+[.\s]+(.*)', line)
            if match_soal:
                soal_text = match_soal.group(1)
                options = []
                ans_key = ""
                found_ans = False
                i += 1
                
                while i < len(raw_lines):
                    curr = raw_lines[i]
                    curr_up = curr.upper().strip()
                    curr_clean = re.sub(r'[^A-Z]', '', curr_up)
                    
                    # Stop jika bertemu header mode baru
                    if any(m in curr_clean for m in ["MULTIPLECHOICE", "MULTIPLEANSWER", "ESSAY", "URAIAN"]):
                        break
                    
                    # Deteksi Label Kunci Jawaban
                    if curr_up.startswith("ANS"):
                        # Ambil semua huruf A-D setelah kata Ans
                        ans_key = ",".join(re.findall(r'[A-D]', curr_up))
                        found_ans = True
                        i += 1; break
                    
                    # Deteksi Opsi (a. b. c. d.)
                    if re.match(r'^[a-fA-F][.\s)]+', curr.strip()):
                        options.append(re.sub(r'^[a-fA-F][.\s)]+', '', curr).strip())
                    else:
                        # Jika bukan opsi dan bukan ANS, berarti sambungan teks soal
                        if len(options) == 0:
                            soal_text += " " + curr
                        else:
                            # Jika sudah ada opsi, sambungkan ke opsi terakhir
                            options[-1] += " " + curr
                    i += 1
                
                if found_ans and options:
                    is_multiple = (current_mode == "MULTIPLE ANSWER")
                    correct_labels = [x.strip() for x in ans_key.split(",")]
                    
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {global_q_num:02d}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                    xml_output += f'    <single>{"false" if is_multiple else "true"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    xml_output += f'    <answernumbering>abc</answernumbering>\n'
                    
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

        # --- 3. PROSES DATA: ESSAY (GABUNGAN) ---
        else:
            essay_text = ""
            found_ans_essay = False
            while i < len(raw_lines):
                curr_line = raw_lines[i]
                curr_up = curr_line.upper().strip()
                if curr_up.startswith("ANS"):
                    found_ans_essay = True
                    i += 1; break
                
                # Masukkan semua teks (termasuk angka 1-5) ke dalam satu konten
                essay_text += curr_line + "<br/>"
                i += 1
            
            if found_ans_essay and essay_text.strip():
                xml_output += f'  <question type="essay">\n'
                xml_output += f'    <name><text>Soal {global_q_num:02d} (Essay)</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_text)}</p>]]></text></questiontext>\n'
                xml_output += '    <defaultgrade>1.0000000</defaultgrade>\n'
                xml_output += '    <responseformat>editor</responseformat>\n'
                xml_output += '  </question>\n'
                stats["ESSAY"] = stats.get("ESSAY", 0) + 1
                global_q_num += 1
            continue

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket
