import re
import base64
from docx import Document
from utils import wrap_arabic

# =========================
# BACA DOCX (TEXT + IMAGE INLINE)
# =========================
def read_docx_content(docx_file):
    doc = Document(docx_file)
    content = []

    for p in doc.paragraphs:
        text = p.text.strip()

        # cek gambar inline
        drawings = p._element.xpath('.//w:drawing')

        # ambil gambar (jika ada)
        if drawings:
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    img_data = rel.target_part.blob
                    encoded = base64.b64encode(img_data).decode()
                    content.append({
                        "type": "image",
                        "data": encoded
                    })

        # ambil teks
        if text:
            content.append({
                "type": "text",
                "data": text
            })

    return content


# =========================
# BUILD XML SOAL
# =========================
def build_question(xml, stats, logs, q_text, options, ans, q_num):

    correct = [x.strip() for x in ans.split(",") if x.strip()]
    correct = list(dict.fromkeys(correct))

    is_multi = len(correct) > 1

    xml += f'<question type="multichoice">\n'
    xml += f'<name><text>Soal {q_num}</text></name>\n'
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

    logs.append(f"✅ Soal {q_num} OK | ANS: {correct}")
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

        # ================= TEXT =================
        if item["type"] == "text":
            line = item["data"]
            up = line.upper()
            clean = re.sub(r'[^A-Z]', '', up)

            # ===== MODE =====
            if "MULTIPLECHOICE" in clean:
                mode = "MC"
                continue

            if "ESSAY" in clean or "URAIAN" in clean:
                mode = "ESSAY"
                continue

            # ===== SOAL BARU =====
            match_q = re.match(r'^(\d+)[.\s)\-:]+(.*)', line)

            if match_q:
                # 🔥 SIMPAN SOAL SEBELUMNYA (FIX BUG 1 SOAL)
                if q_text:
                    if options and ans:
                        xml, stats, logs = build_question(
                            xml, stats, logs, q_text, options, ans, q_num
                        )
                        q_num += 1
                    else:
                        logs.append(f"❌ Soal {q_num} tidak lengkap (skip)")

                # reset
                q_text = match_q.group(2)
                options = []
                ans = ""
                continue

            # ===== ANS =====
            if up.startswith("ANS"):
                match_ans = re.search(r'ANS\s*[:\-]?\s*([A-Z,\s]+)', up)
                if match_ans:
                    ans = match_ans.group(1)
                continue

            # ===== OPSI =====
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

    # 🔥 SIMPAN SOAL TERAKHIR
    if q_text:
        if options and ans:
            xml, stats, logs = build_question(
                xml, stats, logs, q_text, options, ans, q_num
            )
        else:
            logs.append(f"❌ Soal terakhir tidak lengkap")

    xml += '</quiz>'

    return xml, stats, logs, judul_paket
