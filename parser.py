import re
from docx import Document
from utils import wrap_arabic, clean_line

def parse_docx_to_moodle(docx_file):
    """
    FILE: parser.py
    FUNGSI: Scan data, konversi struktur soal, dan proses logika XML Moodle.
    """
    doc = Document(docx_file)
    # Scan data: Ambil semua paragraf, bersihkan spasi, abaikan baris kosong
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

        # --- 1. DETEKSI TRANSISI MODE (KONVERSI DATA) ---
        if "MULTIPLE CHOICE SET" in line_up:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; continue
        elif "MULTIPLE CHOICE" in line_up:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in line_up or "URAIAN" in line_up:
            current_mode = "ESSAY"
            i += 1; continue

        # --- 2. PROSES DATA: PILIHAN GANDA (SINGLE & SET) ---
        if current_mode != "ESSAY":
            # Baris dianggap awal soal jika bukan kunci jawaban (ANS)
            if not line_up.startswith("ANS") and len(line) > 5:
                soal_text = line
                options = []
                ans_key = ""
                i += 1
                
                # Kumpulkan opsi sampai bertemu penanda ANS
                while i < len(raw_lines):
                    curr = raw_lines[i]
                    curr_up = curr.upper()
                    
                    # Berhenti jika menabrak mode lain
                    if any(m in curr_up for m in ["MULTIPLE CHOICE", "ESSAY"]): break
                    
                    # Deteksi Kunci Jawaban
                    if curr_up.startswith("ANS"):
                        ans_key = ",".join(re.findall(r'[A-D]', curr_up))
                        i += 1; break
                    
                    # Ambil opsi (maksimal 6), sisanya sambung ke teks soal
                    if len(options) < 6:
                        options.append(curr)
                    else:
                        soal_text += "<br/>" + curr
                    i += 1
                
                # Generate XML untuk PG
                if options and ans_key:
                    is_single = "SET" not in current_mode
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {q_num_internal:02d}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                    xml_output += f'    <single>{"true" if is_single else "false"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    
                    for idx, opt in enumerate(options):
                        lbl = chr(65 + idx) # A, B, C, D...
                        if is_single:
                            frac = "100" if lbl in ans_key else "0"
                        else:
                            corrects = ans_key.split(",")
                            frac = str(round(100/len(corrects), 5)) if lbl in corrects else "0"
                        
                        xml_output += f'    <answer fraction="{frac}" format="html">\n'
                        xml_output += f'      <text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
                        xml_output += f'    </answer>\n'
                    
                    xml_output += '  </question>\n'
                    stats[current_mode] += 1
                    q_num_internal += 1
                continue
            else:
                i += 1

        # --- 3. PROSES DATA: ESSAY (KOMPONEN: NO SOAL, ISI, ANS) ---
        else:
            # Deteksi Nomor Soal (Auto numbering level 1: 1., 2., dst)
            match_essay = re.match(r'^(\d+)[.\s]+(.*)', line)
            
            if match_essay:
                num_soal = match_essay.group(1)
                essay_content = match_essay.group(2)
                i += 1
                
                # Ambil semua baris di bawahnya sampai ketemu ANS atau nomor baru
                while i < len(raw_lines):
                    curr_line = raw_lines[i]
                    curr_up = curr_line.upper()
                    
                    # Pemutus: Jika bertemu ANS atau Nomor Soal Baru
                    if curr_up.startswith("ANS"):
                        i += 1 # Lewati baris ANS
                        break
                    if re.match(r'^(\d+)[.\s]+', curr_line):
                        break
                        
                    essay_content += "<br/>" + curr_line
                    i += 1
                
                # Generate XML untuk Essay
                xml_output += f'  <question type="essay">\n'
                xml_output += f'    <name><text>Soal Essay {num_soal}</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_content)}</p>]]></text></questiontext>\n'
                xml_output +=
