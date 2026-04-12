import re
import base64
from docx2python import docx2python
from docx import Document
from utils import wrap_arabic

# =========================
# AMBIL GAMBAR
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
# PARSER UTAMA
# =========================
def parse_docx_to_moodle(docx_file):
    try:
        with docx2python(docx_file) as doc_extract:
            full_text = doc_extract.text
            raw_lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    except Exception as e:
        return None, {}, [], f"Error membaca file: {str(e)}"

    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen tidak valid."

    images = extract_images(docx_file)
    img_index = 0

    judul_paket = f"{raw_lines[0]} - {raw_lines[1]}"
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    logs = []
    i = 0
    q_num = 1
    mode = "MC"

    while i < len(raw_lines):
        line = raw_lines[i]
        up = line.upper()
        clean = re.sub(r'[^A-Z]', '', up)

        # ================= MODE =================
        if "MULTIPLECHOICE" in clean:
            mode = "MC"
            i += 1
            continue

        if "ESSAY" in clean or "URAIAN" in clean:
            mode = "ESSAY"
            i += 1
            continue

        # ================= PILIHAN GANDA =================
        if mode != "ESSAY":

            match_q = re.match(r'^(\d+)[.\s)\-:]+(.*)', line)

            if match_q:
                q_text = match_q.group(2)
                options = []
                ans = ""
                found_ans = False
                i += 1

                # sisipkan gambar (jika ada)
                if img_index < len(images):
                    q_text += f'<br><img src="data:image/png;base64,{images[img_index]}" />'
                    img_index += 1

                while i < len(raw_lines):
                    curr = raw_lines[i]
                    curr_up = curr.upper()

                    if re.match(r'^\d+[.\s)\-:]+', curr):
                        break

                    if curr_up.startswith("ANS"):
                        ans = ",".join(re.findall(r'[A-Z]', curr_up))
                        found_ans = True
                        i += 1
                        break

                    match_opt = re.match(r'^([a-zA-Z])[.\s)\-:]+(.*)', curr)
                    if match_opt:
                        options.append(match_opt.group(2))
                    else:
                        if not options:
                            q_text += " " + curr
                        else:
                            options[-1] += " " + curr
                    i += 1

                # VALIDASI
                if not found_ans:
                    logs.append(f"❌ Soal {q_num} tanpa ANS")
                    continue

                if len(options) < 2:
                    logs.append(f"❌ Soal {q_num} opsi kurang")
                    continue

                correct = [x.strip() for x in ans.split(",") if x.strip()]
                is_multi = len(correct) > 1

                # ================= XML =================
                xml += f'<question type="multichoice">\n'
                xml += f'<name><text>Soal {q_num}</text></name>\n'
                xml += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(q_text)}]]></text></questiontext>\n'
                xml += f'<defaultgrade>1.0</defaultgrade>\n'
                xml += f'<single>{"false" if is_multi else "true"}</single>\n'
                xml += f'<shuffleanswers>true</shuffleanswers>\n'

                for idx, opt in enumerate(options):
                    label = chr(65 + idx)

                    if is_multi:
                        frac = str(round(100/len(correct), 5)) if label in correct else "0"
                    else:
                        frac = "100" if label in correct else "0"

                    xml += f'<answer fraction="{frac}">\n'
                    xml += f'<text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
                    xml += f'</answer>\n'

                xml += '</question>\n'

                if is_multi:
                    stats["MULTIPLE CHOICE SET"] += 1
                else:
                    stats["MULTIPLE CHOICE"] += 1

                logs.append(f"✅ Soal {q_num} OK")
                q_num += 1
                continue

            else:
                i += 1

        # ================= ESSAY =================
        else:
            essay = ""

            while i < len(raw_lines):
                curr = raw_lines[i]

                if curr.upper().startswith("ANS"):
                    i += 1
                    break

                essay += curr + "<br/>"
                i += 1

            if essay.strip():
                xml += f'<question type="essay">\n'
                xml += f'<name><text>Essay {q_num}</text></name>\n'
                xml += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(essay)}]]></text></questiontext>\n'
                xml += '</question>\n'

                stats["ESSAY"] += 1
                logs.append(f"✅ Essay {q_num}")
                q_num += 1

    xml += '</quiz>'

    return xml, stats, logs, judul_paket
