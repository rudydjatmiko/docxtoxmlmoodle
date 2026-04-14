import re
import base64
import uuid
from docx import Document
import xml.etree.ElementTree as ET


def is_option(text):
    return re.match(r'^[A-D][\.\)]\s*', text.strip()) is not None


def extract_answer_key(text):
    if "ANS:" in text.upper():
        ans = text.upper().split("ANS:")[1].strip()
        return [a.strip() for a in ans.split(",")]
    return []


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


def parse_docx_to_moodle(file, moodle_type="multichoice"):

    doc = Document(file)
    quiz = ET.Element("quiz")

    questions = []

    buffer_text = []
    buffer_answers = []
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

        # OPTION
        if is_option(text):
            buffer_answers.append(text)
            continue

        # IMAGE
        for run in para.runs:
            img = extract_image_from_run(run)
            if img:
                buffer_images.append(img)

        # ANSWER KEY (END OF QUESTION)
        if "ANS:" in text.upper():
            correct_answers = extract_answer_key(text)

            questions.append({
                "text": "<br/>".join(buffer_text),
                "answers": buffer_answers,
                "images": buffer_images,
                "correct": correct_answers
            })

            # RESET
            buffer_text = []
            buffer_answers = []
            buffer_images = []
            correct_answers = []

            continue

        # NORMAL TEXT
        buffer_text.append(text)

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

            for ans in q["answers"]:
                label = ans[0].upper()
                fraction = "100" if label in q["correct"] else "0"

                a = ET.SubElement(question, "answer", fraction=fraction, format="html")
                ET.SubElement(a, "text").text = f"<![CDATA[{ans}]]>"

    xml_str = ET.tostring(quiz, encoding="utf-8").decode("utf-8")

    return xml_str, stats, [], "Parsing selesai"
