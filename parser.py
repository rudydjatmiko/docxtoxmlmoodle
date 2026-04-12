import re
from doc2python import doc2python
from utils import wrap_arabic

def parse_docx_to_moodle(docx_file):
    try:
        with doc2python(docx_file) as doc_extract:
            full_text = doc_extract.text
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
        clean_header = re.sub(r'[^A-Z]', '', line_up)

        # ================= MODE =================
        if "MULTIPLEANSWER" in clean_header:
            current_mode = "MULTIPLE ANSWER"
            i += 1; continue
        elif "MULTIPLECHOICE" in clean_header:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue
        elif "ESSAY" in clean_header or "URAIAN" in clean_header:
            current_mode = "ESSAY"
            i += 1; continue

        # ================= PILIHAN GANDA =================
        if current_mode != "ESSAY":

            match_soal = re.match(r'^(\d+)[.\s)\-:]+(.*)', line)

            if match_soal:
                soal_text = match_soal.group(2).strip()
                options = []
                ans_key = ""
                found_ans = False
                i += 1

                while i < len(raw_lines):
                    curr = raw_lines[i]
                    curr_up = curr.upper().strip()
                    curr_clean = re.sub(r'[^A-Z]', '', curr_up)

                    # stop kondisi
                    if any(m in curr_clean for m in ["MULTIPLECHOICE", "MULTIPLEANSWER", "ESSAY", "URAIAN"]):
                        break
                    if re.match(r'^\d+[.\s)\-:]+', curr):
                        break

                    # ================= ANS =================
                    if curr_up.startswith("ANS"):
                        ans_key = ",".join(re.findall(r'[A-Z]', curr_up))
                        found_ans = True
                        i += 1
                        break

                    # ================= OPSI =================
                    match_opt = re.match(r'^([a-zA-Z])[.\s)\-:]+(.*)', curr)
                    if match_opt:
                        options.append(match_opt.group(2).strip())
                    else:
                        # lanjutan teks
                        if not options:
                            soal_text += " " + curr
                        else:
                            options[-1] += " " + curr
                    i += 1

                # ================= VALIDASI =================
                if not found_ans:
                    audit_log.append(f"❌ Soal {global_q_num} tidak memiliki ANS")
                    continue

                if len(options) < 2:
                    audit_log.append(f"❌ Soal {global_q_num} opsi kurang")
                    continue

                # ================= XML =================
                is_multiple = (current_mode == "MULTIPLE ANSWER")

                xml_output += f'  <question type="multichoice">\n'
                xml_output += f'    <name><text>Soal {global_q_num:02d}</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(soal_text)}</p>]]></text></questiontext>\n'
                xml_output += f'    <defaultgrade>1.0000000</defaultgrade>\n'
                xml_output += f'    <single>{"false" if is_multiple else "true"}</single>\n'
                xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                xml_output += f'    <answernumbering>abc</answernumbering>\n'

                correct_list = ans_key.split(",")

                for idx, opt in enumerate(options):
                    lbl = chr(65 + idx)

                    if is_multiple:
                        frac = str(round(100/len(correct_list), 5)) if lbl in correct_list else "0"
                    else:
                        frac = "100" if lbl in correct_list else "0"

                    xml_output += f'    <answer fraction="{frac}" format="html">\n'
                    xml_output += f'      <text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
                    xml_output += f'    </answer>\n'

                xml_output += '  </question>\n'

                stats[current_mode] = stats.get(current_mode, 0) + 1
                audit_log.append(f"✅ Soal {global_q_num} berhasil diproses")
                global_q_num += 1
                continue

            else:
                i += 1

        # ================= ESSAY =================
        else:
            essay_text = ""
            found_ans_essay = False

            while i < len(raw_lines):
                curr_line = raw_lines[i]

                if curr_line.upper().startswith("ANS"):
                    found_ans_essay = True
                    i += 1
                    break

                essay_text += curr_line + "<br/>"
                i += 1

            if found_ans_essay and essay_text.strip():
                xml_output += f'  <question type="essay">\n'
                xml_output += f'    <name><text>Soal {global_q_num:02d} (Essay)</text></name>\n'
                xml_output += f'    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_text)}</p>]]></text></questiontext>\n'
                xml_output += '    <responseformat>editor</responseformat>\n'
                xml_output += '  </question>\n'

                stats["ESSAY"] = stats.get("ESSAY", 0) + 1
                audit_log.append(f"✅ Essay {global_q_num} berhasil")
                global_q_num += 1
            else:
                audit_log.append(f"❌ Essay {global_q_num} tidak valid")

            continue

    xml_output += '</quiz>'

    return xml_output, stats, audit_log, judul_paket
