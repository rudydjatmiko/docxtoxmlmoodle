import re
import base64
import uuid
from docx import Document
import xml.etree.ElementTree as ET


# =========================
# CLEAN TEXT
# =========================
def clean_text(text):
    return text.strip().replace("  ", " ")


# =========================
# FORMAT HTML (KUNCI UTAMA)
# =========================
def format_html(lines):
    html = ""
    in_list = False

    for line in lines:
        line = clean_text(line)

        # LIST: 1) 2) 3)
        if re.match(r'^\d+\)', line):
            if not in_list:
                html += "<ul>"
                in_list = True
            html += f"<li>{line}</li>"

        else:
            if in_list:
                html += "</ul>"
                in_list = False
            html += f"<p>{line}</p>"

    if in_list:
        html += "</ul>"

    return html


# =========================
# CLEAN OPTION
# =========================
def clean_option(text):
    return re.sub(r'^[A-D][\.\)]\s*', '', text).strip()


# =========================
# ANSWER KEY
# =========================
def extract_answer_key(text):
    if "ANS:" in text.upper():
        ans = text.upper().split("ANS:")[1].strip()
        return [a.strip() for a in ans.split(",")]
    return []


# =========================
# IMAGE HANDLER
# =========================
def extract_image_from_run(run):
    if 'graphic' not in run._element.xml:
        return None

    try:
        blips = run._element.xpath('.//a:blip')
        if not blips:
            return None

        embed = blips[0].get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        )

        image_part = run.part.related_parts[embed]
        image_bytes = image_part.blob

        filename = f"{uuid.uuid4().hex}.jpg"
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        return {"name": filename, "data": encoded}

    except:
        return None


# =========================
# MAIN PARSER
# =========================
def parse_docx_to_moodle(file, moodle_type="multichoice"):

    doc = Document(file)
    quiz = ET.Element("quiz")

    questions = []

    buffer_lines = []
    buffer_images = []
    correct_answers = []

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    for para in doc.paragraphs:

        text = para.text.strip()
        if not text:
            continue

        # IMAGE
        for run in para.runs:
            img = extract_image_from_run(run)
            if img:
                buffer_images.append(img)

        # END OF QUESTION
        if "ANS:" in text.upper():

            correct_answers = extract_answer_key(text)

            # SPLIT
            if len(buffer_lines) >= 4:
                question_text = buffer_lines[:-4]
                options = buffer_lines[-4:]
            else:
                question_text = buffer_lines
                options = []

            options = [clean_option(o) for o in options]

            questions.append({
                "text_lines": question_text,
                "answers": options,
                "images": buffer_images,
                "correct": correct_answers
            })

            buffer_lines = []
            buffer_images = []
            correct_answers = []

            continue

        buffer_lines.append(text)

    # =========================
    # BUILD XML
    # =========================
    for i, q in enumerate(questions):

        if len(q["answers"]) == 0:
            qtype = "essay"
            stats["ESSAY"] += 1

        elif len(q["correct"]) > 1:
            qtype = "multichoiceset"
            stats["MULTIPLE CHOICE SET"] += 1

        else:
            qtype = "multichoice"
            stats["MULTIPLE CHOICE"] += 1

        question = ET.SubElement(quiz, "question", type=qtype)

        # NAME
        name = ET.SubElement(question, "name")
        ET.SubElement(name, "text").text = f"Soal {i+1:02d}"

        # QUESTION TEXT
        qtext = ET.SubElement(question, "questiontext", format="html")
        text_el = ET.SubElement(qtext, "text")

        # 🔥 FORMAT HTML (FIX UTAMA)
        html = format_html(q["text_lines"])

        # IMAGE
        for img in q["images"]:
            html += f'<p><img src="@@PLUGINFILE@@/{img["name"]}"/></p>'

        text_el.text = f"<![CDATA[{html}]]>"

        # FILE IMAGE
        for img in q["images"]:
            file_el = ET.SubElement(qtext, "file", name=img["name"], encoding="base64")
            file_el.text = img["data"]

        # =========================
        # ANSWER
        # =========================
        if qtype != "essay":

            single = ET.SubElement(question, "single")
            single.text = "false" if qtype == "multichoiceset" else "true"

            ET.SubElement(question, "shuffleanswers").text = "true"
            ET.SubElement(question, "answernumbering").text = "abc"

            labels = ["A", "B", "C", "D"]

            for idx, ans in enumerate(q["answers"]):

                fraction = "100" if labels[idx] in q["correct"] else "0"

                a = ET.SubElement(question, "answer", fraction=fraction, format="html")
                ET.SubElement(a, "text").text = f"<![CDATA[{clean_text(ans)}]]>"

    xml_str = ET.tostring(quiz, encoding="utf-8").decode("utf-8")

    return xml_str, stats, [], "Parsing selesai"
