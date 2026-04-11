import streamlit as st
from docx import Document
import re

def wrap_arabic(text):
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    # Sanitasi teks dari karakter non-breaking space (\xa0)
    raw_lines = [p.text.replace('\xa0', ' ').strip() for p in doc.paragraphs if p.text.strip()]
    
    if not raw_lines: return None, {}, [], "File Kosong"

    judul_paket = f"{raw_lines[0]} {raw_lines[1]}" if len(raw_lines) > 1 else raw_lines[0]
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    current_mode = "MULTIPLE CHOICE"
    q_num_internal = 1
    stats = {"MULTIPLE CHOICE": 0, "MULTIPLE CHOICE SET": 0, "ESSAY": 0}
    audit_log = []
    
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        line_up = line.upper()

        # 1. DETEKSI TIPE SOAL (PENANDA MODE) - PRIORITAS UTAMA
        if "MULTIPLE CHOICE SET" in line_up:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1; continue
        elif "MULTIPLE CHOICE" in line_up:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in line_up:
            current_mode = "ESSAY"
            i += 1; continue

        # 2. DETEKSI NOMOR SOAL (LEVEL 1: ANGKA)
        match_soal = re.match(r'^\s*(\d+)[\.\s]+(.*)', line)
        
        if match_soal and current_mode != "ESSAY":
            soal_num_doc = match_soal.group(1)
            soal_text = match_soal.group(2)
            options = []
            ans_key = ""
            i += 1
            
            # Kumpulkan baris sampai ketemu ANS:
            while i < len(raw_lines):
                curr_line = raw_lines[i]
                curr_up = curr_line.upper()
                
                # Cek Penanda Tipe Soal baru di tengah jalan (antisipasi error format)
                if any(x in curr_up for x in ["MULTIPLE CHOICE", "ESSAY"]):
                    break

                # 4. DETEKSI KUNCI JAWABAN (ANS:)
                if curr_up.startswith("ANS:"):
                    # Cek apakah kunci ada di baris yang sama (misal Ans: A)
                    found_key = "".join(re.findall(r'[A-D,]', curr_up.replace("ANS:", "")))
                    if found_key:
                        ans_key = found_key
                    else:
                        # Jika baris ANS: kosong, ambil baris di bawahnya
                        i += 1
                        if i < len(raw_lines):
                            ans_key = "".join(re.findall(r'[A-D,]', raw_lines[i].upper()))
                    i += 1
                    break
                
                # 3. DETEKSI OPSI JAWABAN (LEVEL 2: HURUF)
                match_opt = re.match(r'^\s*([a-dA-D])[\.\)\-\s]+(.*)', curr_line)
                if match_opt:
                    options.append(match_opt.group(2).strip())
                else:
                    # Jika bukan angka baru dan bukan opsi, berarti lanjutan teks soal
                    if not re.match(r'^\s*\d+[\.\s]+', curr_line):
                        soal_text += " " + curr_line
                    else:
                        # Jika ketemu angka baru sebelum ada ANS:, soal sebelumnya dianggap gagal
                        break
                i += 1
            
            # VALIDASI DAN GENERASI XML
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
                audit_log.append(f"✅ No {soal_num_doc}: Berhasil ({current_mode})")
                q_num_internal += 1
            else:
                audit_log.append(f"❌ No {soal_num_doc}: Gagal (Opsi/Kunci tidak lengkap)")
            continue

        elif current_mode == "ESSAY":
            # Mode Essay: Ambil sisa teks sebagai satu kesatuan
            essay_content = "<br/>".join(raw_lines[i:])
            essay_content = re.sub(r'Ans:.*', '', essay_content, flags=re.IGNORECASE | re.DOTALL)
            xml_output += f'  <question type="essay">\n    <name><text>Soal {q_num_internal:02d} (Essay)</text></name>\n'
            xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_content)}</p>]]></text></questiontext>\n'
            xml_output += '    <responseformat>editor</responseformat><responserequired>1</responserequired>\n  </question>\n'
            stats["ESSAY"] += 1
            audit_log.append(f"✅ Bagian Essay Berhasil")
            break
        else:
            i += 1

    xml_output += '</quiz>'
    return xml_output, stats, audit_log, judul_paket

# --- UI STREAMLIT (Tetap Sama) ---
