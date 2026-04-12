import re
import base64
from docx import Document
from utils import wrap_arabic


# =========================
# NORMALIZE TEXT (ANTI BUG WORD)
# =========================
def normalize(text):
    return re.sub(r'\s+', ' ', text).strip().upper()


# =========================
# READ DOCX (TEXT + INLINE IMAGE)
# =========================
def read_docx_content(docx_file):
    doc = Document(docx_file)
    content = []

    for p in doc.paragraphs:

        # === IMAGE (INLINE + MATHTYPE) ===
        drawings = p._element.xpath('.//w:drawing')

        if drawings:
            for drawing in drawings:
                blips = drawing.xpath('.//a:blip')

                for blip in blips:
                    rId = blip.get(
                        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                    )

                    if rId in doc.part.rels:
                        img_part = doc.part.rels[rId].target_part
                        img_data = img_part.blob
                        encoded = base64.b64encode(img_data).decode()

                        content.append({
                            "type": "image",
                            "data": encoded
                        })

        # === TEXT ===
        text = p.text.strip()
        if text:
            content.append({
                "type": "text",
                "data": text
            })

    return content


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
    xml += f'<defaultgrade>1.0</defaultgrade>\n'
    xml += f'<single>{"false" if is_multi else "true"}</single>\n'
    xml += f'<shuffleanswers>true</shuffleanswers>\n'

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

    logs.append(f"✅ Soal {q_num:02d} OK | ANS: {correct}")
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
# PARSER UTAMA
# =========================
def parse_docx_to_moodle(docx_file):

    content = read_docx_content(docx_file)

    if len(content) < 3:
        return None, {}, [], "Dokumen tidak valid."

    judul_paket = f"{content[0]['data']} - {content[1]['data']}"
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    logs = []

    q_num = 1
    mode = "MC"

    q_text = ""
    options = []
    ans = ""

    for item in content:

        if item["type"] == "text":
            line = item["data"]
            norm = normalize(line)

            # ================= MODE =================
            if "MULTIPLE" in norm and "CHOICE" in norm:
                mode = "MC"
                continue

            if norm in ["ESSAY", "URAIAN"]:
                mode = "ESSAY"
                q_text = ""
                continue

            # ================= ESSAY =================
            if mode == "ESSAY":

                match_q = re.match(r'^(\d+)[.\s)\-:]+(.*)', line)

                if match_q:
                    if q_text:
                        xml, stats, logs = build_essay(
                            xml, stats, logs, q_text, ans, q_num
                        )
                        q_num += 1

                    q_text = match_q.group(2)
                    ans = ""
                    continue

                if norm.startswith("ANS"):
                    match_ans = re.search(r'ANS\s*[:\-]?\s*(.*)', line)
                    ans = match_ans.group(1).strip() if match_ans else ""

                    xml, stats, logs = build_essay(
                        xml, stats, logs, q_text, ans, q_num
                    )
                    q_num += 1

                    q_text = ""
                    ans = ""
                    continue

                q_text += line + "<br/>"
                continue

            # ================= MC =================
            match_q = re.match(r'^(\d+)[.\s)\-:]+(.*)', line)

            if match_q:

                if q_text:
                    if options and ans:
                        xml, stats, logs = build_mc(
                            xml, stats, logs, q_text, options, ans, q_num
                        )
                        q_num += 1
                    else:
                        logs.append(f"❌ Soal {q_num:02d} tidak lengkap")

                q_text = match_q.group(2)
                options = []
                ans = ""
                continue

            if norm.startswith("ANS"):
                match_ans = re.search(r'ANS\s*[:\-]?\s*([A-Z,\s]+)', norm)
                ans = match_ans.group(1) if match_ans else ""
                continue

            match_opt = re.match(r'^([A-Da-d])[.\s)\-:]+(.*)', line)

            if match_opt:
                options.append(match_opt.group(2))
            else:
                if options:
                    options[-1] += "<br/>" + line
                else:
                    q_text += "<br/>" + line

        # ================= IMAGE =================
        elif item["type"] == "image":
            img_html = f'<br><img src="data:image/png;base64,{item["data"]}" />'

            if options:
                options[-1] += img_html
            else:
                q_text += img_html

    # ================= FINAL SAVE =================
    if q_text and options and ans:
        xml, stats, logs = build_mc(
            xml, stats, logs, q_text, options, ans, q_num
        )

    xml += '</quiz>'

    return xml, stats, logs, judul_paket
