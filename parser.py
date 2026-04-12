import re
import base64
from docx2python import docx2python
from docx import Document
from utils import wrap_arabic


# =========================
# NORMALIZE TEXT
# =========================
def normalize(text):
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')
    text = text.replace('\t', ' ')
    return re.sub(r'\s+', ' ', text).strip().upper()


# =========================
# AMBIL GAMBAR DARI DOCX
# =========================
def extract_images(docx_file):
    doc = Document(docx_file)
    images = []

    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            img_data = rel.target_part.blob
            encoded = base64.b64encode(img_data).decode()
            images.append(encoded)

    return images


# =========================
# BUILD MC
# =========================
def build_mc(xml, stats, logs, q_text, options, ans, q_num):

    correct = [x.strip() for x in ans.split(",") if x.strip()]
    correct = list(dict.fromkeys(correct))
    is_multi = len(correct) > 1

    xml += f'<question type="multichoice">\n'
    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'
    xml += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(q_text)}]]></text></questiontext>\n'
    xml += f'<single>{"false" if is_multi else "true"}</single>\n'

    for i, opt in enumerate(options):
        label = chr(65 + i)

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

    logs.append(f"✅ Soal {q_num:02d} | ANS: {correct}")
    return xml, stats, logs


# =========================
# BUILD ESSAY
# =========================
def build_essay(xml, stats, logs, q_text, ans, q_num):

    xml += f'<question type="essay">\n'
    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'
    xml += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(q_text)}]]></text></questiontext>\n'

    if ans and ans != "-":
        xml += f'<generalfeedback format="html">\n'
        xml += f'<text><![CDATA[<b>Referensi jawaban:</b><br>{wrap_arabic(ans)}]]></text>\n'
        xml += f'</generalfeedback>\n'

    xml += '</question>\n'

    stats["ESSAY"] += 1
    logs.append(f"✅ Essay {q_num:02d}")
    return xml, stats, logs


# =========================
# PARSER UTAMA (HYBRID)
# =========================
def parse_docx_to_moodle(docx_file):

    try:
        # ===== TEXT VIA DOC2PYTHON =====
        with doc2python(docx_file) as doc:
            raw_text = doc.text

        raw_lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    except Exception as e:
        return None, {}, [], f"Error membaca file: {str(e)}"

    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen tidak valid."

    judul_paket = f"{raw_lines[0]} - {raw_lines[1]}"

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    logs = []

    q_num = 1
    q_text = ""
    options = []
    ans = ""

    for line in raw_lines:

        norm = normalize(line)

        # ================= SOAL BARU =================
        match_q = re.match(r'^(\d+)[.\s]+(.*)', line)

        if match_q:

            # simpan soal sebelumnya
            if q_text:
                if options:
                    xml, stats, logs = build_mc(
                        xml, stats, logs, q_text, options, ans, q_num
                    )
                else:
                    xml, stats, logs = build_essay(
                        xml, stats, logs, q_text, ans, q_num
                    )
                q_num += 1

            q_text = match_q.group(2)
            options = []
            ans = ""
            continue

        # ================= ANS =================
        if norm.startswith("ANS"):

            match_ans_mc = re.search(r'ANS\s*[:\-]?\s*([A-Z,\s]+)', norm)
            match_ans_es = re.search(r'ANS\s*[:\-]?\s*(.*)', line)

            if options:
                ans = match_ans_mc.group(1) if match_ans_mc else ""
            else:
                ans = match_ans_es.group(1) if match_ans_es else ""

            continue

        # ================= OPSI =================
        match_opt = re.match(r'^([A-Da-d])[.\s]+(.*)', line)

        if match_opt:
            options.append(match_opt.group(2))
        else:
            if options:
                options[-1] += "<br/>" + line
            else:
                q_text += "<br/>" + line

    # ================= SOAL TERAKHIR =================
    if q_text:
        if options:
            xml, stats, logs = build_mc(
                xml, stats, logs, q_text, options, ans, q_num
            )
        else:
            xml, stats, logs = build_essay(
                xml, stats, logs, q_text, ans, q_num
            )

    xml += '</quiz>'

    return xml, stats, logs, judul_paket
