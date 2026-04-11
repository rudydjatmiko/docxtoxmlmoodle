import re
from docx import Document
from utils import wrap_arabic, clean_line

def parse_docx_to_moodle(docx_file):
    """
    Blok Parser: Membedah isi dokumen Word menjadi format Moodle XML.
    """
    doc = Document(docx_file)
    # Scan data: Mengambil semua paragraf dan membersihkan spasi aneh
    raw_lines = [clean_line(p.text) for p in doc.paragraphs if p.text.strip()]
    
    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen terlalu pendek atau kosong."

    judul_paket = f"{raw_lines[0]} - {raw_lines[1]}"
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    current_mode = "MULTIPLE CHOICE"
    q_num = 1
    stats = {"MULTIPLE CHOICE": 0, "MULTIPLE CHOICE SET": 0, "ESSAY": 0}
    audit_log = []
    
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        line_up = line.upper()

        # Konversi Data: Deteksi Transisi Mode (PG, SET, atau Essay)
        if "MULTIPLE CHOICE SET" in line_up:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; continue
        elif "MULTIPLE CHOICE" in line_up:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in line_up or "URAIAN" in line_up:
            current_mode = "ESSAY"
            i += 1; continue

        # Proses Data: Logika Pilihan Ganda
        if current_mode != "ESSAY":
            if not line_up.startswith("ANS") and len(line) > 5:
                soal_text, options, ans_key = line, [], ""
                i += 1
                
                while i < len(raw_lines):
                    curr = raw_lines[i]
                    if any(m in curr.upper() for m in ["MULTIPLE CHOICE", "ESSAY"]): break
                    if curr.upper().startswith("ANS"):
                        ans_key = ",".join(re.findall(r'[A-D]', curr.upper()))
                        i += 1; break
                    
                    if len(options) < 6:
                        options.append(curr)
                    else:
                        soal_text += "<br/>" + curr
                    i += 1
                
                if options and ans_key:
                    is_single = "SET" not in current_mode
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {q_num}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                    xml_output += f'    <single>{"true" if is_single else "false"}</single>\n'
                    
                    for idx, opt in enumerate(options):
                        lbl = chr(65 + idx)
                        if is_single:
                            frac = "100" if lbl in ans_key else "0"
                        else:
                            corrects = ans_key.split(",")
                            frac = str(round(100/len(corrects), 5)) if lbl in corrects else "0"
                        xml_output += f'    <answer fraction="{frac}" format="html"><text><![CDATA[{wrap_arabic(opt)}]]></text></answer>\n'
                    xml_output += '  </question>\n'
                    stats[current_mode] += 1
                    q_num += 1
                continue
            else: i += 1

        # Proses Data: Logika Essay (Memecah per nomor)
        else:
            match_essay = re.match(r'^(\d+)[.\s]+(.*)', line)
            if match_essay:
                num, txt = match_essay.groups()
                i += 1
                while i < len(raw_lines) and not re.match(r'^\d+[.\s]+', raw_lines[i]):
                    txt += "<br/>" + raw_lines[i]
                    i += 1
                xml_output += f'  <question type="essay">\n    <name><text>Essay {num}</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(txt)}</p>]]></text></questiontext>\n'
                xml_output += '    <responseformat>editor</responseformat></question>\n'
                stats["ESSAY"] += 1
                q_num += 1
            else: i += 1

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket
