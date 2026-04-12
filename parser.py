import re
import base64
from docx2python import docx2python
from docx import Document
from utils import wrap_arabic

# =========================
# AMBIL GAMBAR DARI DOCX
# =========================
def extract_images(docx_file):
    doc = Document(docx_file)
    images = []

    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            encoded = base64.b64encode(image_data).decode("utf-8")
            images.append(encoded)

    return images

# =========================
# MAIN PARSER
# =========================
def parse_docx_to_moodle(docx_file):
    try:
        with docx2python(docx_file) as doc_extract:
            full_text = doc_extract.text
            raw_lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    except Exception as e:
        return None, {}, [], f"Error membaca file: {str(e)}"

    # ambil semua gambar
    images = extract_images(docx_file)
    img_index = 0

    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen tidak valid atau kosong."

    judul_paket = f"{raw_lines[0]} - {raw_lines[1]}"
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'

    current_mode = "MULTIPLE CHOICE"
    global_q_num = 1 

    stats = {
        "MULTIPLE CHOICE": 0,
        "ESSAY": 0
    }

    audit_log = []

    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        line_up = line.upper().strip()
        clean_header = re.sub(r'[^A-Z]', '', line_up)

        # ================= MODE =================
        if "MULTIPLECHOICE" in clean_header:
            current_mode = "MULTIPLE CHOICE"
            i += 1; continue

        elif "ESSAY" in clean_header or "URAIAN" in clean_header:
            current_mode = "ESSAY"
            i += 1; continue

        # ================= PILIHAN GANDA =================
        if current_mode != "ESSAY":

            match_soal = re.match(r'^(\d+)[.\s)\-:]+(.*)', line)

            if match_soal:
                soal_text = match_soal.group(2)
                options = []
                ans_key = ""
                found_ans = False
                i += 1

                # 🔥 jika ada gambar, sisipkan ke soal
                if img_index < len(images):
                    soal_text += f'<br><img src="data:image/png;base64,{images[img_index]}" />'
                    img_index += 1

                while i < len(raw_lines):
                    curr = raw_lines[i]
                    curr_up = curr.upper().strip()
                    curr_clean = re.sub(r'[^A-Z]', '', curr_up)

                    if any(m in curr_clean for m in ["MULTIPLECHOICE", "ESSAY", "URAIAN"]):
                        break
                    if re.match(r'^\d+[.\s)\-:]+', curr):
                        break

                    # ANS
                    if curr_up.startswith("ANS"):
                        ans_key = ",".join(re.findall(r'[A-Z]', curr_up))
                        found_ans = True
                        i += 1
                        break

                    # OPSI
                    match_opt = re.match(r'^([a-zA-Z])[.\s)\-:]+(.*)', curr)
                    if match_opt:
                        options.append(match_opt.group(2))
                    else:
                        if not options:
                            soal_text += " " + curr
                        else:
                            options[-1] += " " + curr
                    i += 1

                # VALIDASI
                if not found_ans or len(options) < 2:
                    audit_log.append(f"❌ Soal {global_q_num} tidak valid")
                    continue

                # DETEKSI SINGLE / MULTI
                correct_list = ans_key.split(",")
                is_multiple = len(correct_list) > 1

                # ================= XML =================
                xml_output += f'<question type="multichoice">\n'
                xml_output += f'<name><text>Soal {global_q_num}</text></name>\n'
                xml_output += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(soal_text)}]]></text></questiontext>\n'
                xml_output += f'<defaultgrade>1.0</defaultgrade>\n'
                xml_output += f'<single>{"false" if is_multiple else "true"}</single>\n'

                for idx, opt in enumerate(options):
                    lbl = chr(65 + idx)

                    if is_multiple:
                        frac = str(100/len(correct_list)) if lbl in correct_list else "0"
                    else:
                        frac = "100" if lbl in correct_list else "0"

                    xml_output += f'<answer fraction="{frac}">\n'
                    xml_output += f'<text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
                    xml_output += f'</answer>\n'

                xml_output += '</question>\n'

                stats["MULTIPLE CHOICE"] += 1
                audit_log.append(f"✅ Soal {global_q_num} OK")
                global_q_num += 1
                continue

            else:
                i += 1

        # ================= ESSAY =================
        else:
            essay_text = ""

            while i < len(raw_lines):
                curr_line = raw_lines[i]

                if curr_line.upper().startswith("ANS"):
                    i += 1
                    break

                essay_text += curr_line + "<br/>"
                i += 1

            if essay_text.strip():
                xml_output += f'<question type="essay">\n'
                xml_output += f'<name><text>Essay {global_q_num}</text></name>\n'
                xml_output += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(essay_text)}]]></text></questiontext>\n'
                xml_output += '</question>\n'

                stats["ESSAY"] += 1
                audit_log.append(f"✅ Essay {global_q_num}")
                global_q_num += 1

    xml_output += '</quiz>'

    return xml_output, stats, audit_log, judul_paket
