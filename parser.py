import re
import base64
import uuid
from docx import Document
import xml.etree.ElementTree as ET


# =========================
# CLEAN OPTION TEXT
# =========================
def clean_option(text):
    return re.sub(r'^[A-D][\.\)]\s*', '', text).strip()


# =========================
# DETECT HEADER (BUANG)
# =========================
def is_header(text):
    keywords = [
        "daily exam",
        "academic year",
        "multiple choice",
        "choose the right answer"
    ]
    text_low = text.lower()
    return any(k in text_low for k in keywords)


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

    started = False  # 🔥 penting untuk skip header

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    for para in doc.paragraphs:

        text = para.text.strip()
        if not text:
            continue

        # =========================
        # SKIP HEADER
        # =========================
        if not started:
            if is_header(text) or len(text) < 5:
                continue
            else:
                started = True

        # =========================
        # IMAGE
        # =========================
        for run in para.runs:
            img = extract_image_from_run(run)
            if img:
                buffer_images.append(img)

        # =========================
        # END OF QUESTION
        # =========================
        if "ANS:" in text.upper():

            correct_answers = extract_answer_key(text)

            # SPLIT TEXT & OPTIONS
            if len(buffer_lines) >= 4:
                question_text = buffer_lines[:-4]
                options = buffer_lines[-4:]
            else:
                question_text = buffer_lines
                options = []

            # CLEAN OPTION
            options = [clean_option(o) for o in options]

            questions.append({
                "text": "<br/>".join(question_text),
                "answers": options,
                "images": buffer_images,
                "correct": correct_answers
            })

            # RESET
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

        name = ET.SubElement(question, "name")
        ET.SubElement(name, "text").text = f"Soal {i+1:02d}"

        qtext = ET.SubElement(question, "questiontext", format="html")
        text_el = ET.SubElement(qtext, "text")

        html = q["text"]

        for img in q["images"]:
            html += f'<br/><img src="@@PLUGINFILE@@/{img["name"]}"/>'

        text_el.text = f"<![CDATA[{html}]]>"

        for img in q["images"]:
            file_el = ET.SubElement(qtext, "file", name=img["name"], encoding="base64")
            file_el.text = img["data"]

        if qtype != "essay":

            single = ET.SubElement(question, "single")
            single.text = "false" if qtype == "multichoiceset" else "true"

            ET.SubElement(question, "shuffleanswers").text = "true"
            ET.SubElement(question, "answernumbering").text = "abc"

            labels = ["A", "B", "C", "D"]

            for idx, ans in enumerate(q["answers"]):

                fraction = "100" if labels[idx] in q["correct"] else "0"

                a = ET.SubElement(question, "answer", fraction=fraction, format="html")
                ET.SubElement(a, "text").text = f"<![CDATA[{ans}]]>"

    xml_str = ET.tostring(quiz, encoding="utf-8").decode("utf-8")

    return xml_str, stats, [], "Parsing selesai"
