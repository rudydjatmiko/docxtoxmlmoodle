import base64
import uuid
from docx import Document
import xml.etree.ElementTree as ET


def is_question(text):
    text = text.strip()
    return text.startswith(tuple([f"{i}." for i in range(1, 100)]))


def extract_image_from_run(run):
    """Ambil gambar dari run (inline image)"""
    if 'graphic' not in run._element.xml:
        return None

    try:
        drawing = run._element.xpath('.//a:blip')
        if not drawing:
            return None

        embed = drawing[0].get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        )

        image_part = run.part.related_parts[embed]
        image_bytes = image_part.blob

        filename = f"{uuid.uuid4().hex}.jpg"
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        return {
            "name": filename,
            "data": encoded
        }

    except Exception:
        return None


def parse_docx_to_moodle(file, moodle_type="multichoice"):

    doc = Document(file)

    quiz = ET.Element("quiz")

    current_question = None
    current_answers = []
    current_text = ""
    current_images = []

    questions = []

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    for para in doc.paragraphs:

        text = para.text.strip()

        # =========================
        # DETEKSI SOAL BARU
        # =========================
        if is_question(text):

            if current_question:
                questions.append({
                    "text": current_text,
                    "answers": current_answers,
                    "images": current_images
                })

            current_question = True
            current_text = text
            current_answers = []
            current_images = []

        else:
            if current_question:
                current_text += "<br/>" + text

        # =========================
        # DETEKSI GAMBAR INLINE
        # =========================
        for run in para.runs:
            img = extract_image_from_run(run)
            if img and current_question:
                current_images.append(img)

        # =========================
        # DETEKSI JAWABAN
        # =========================
        if text.startswith(tuple("ABCD")):
            current_answers.append(text)

    # append terakhir
    if current_question:
        questions.append({
            "text": current_text,
            "answers": current_answers,
            "images": current_images
        })

    # =========================
    # BUILD XML
    # =========================
    for i, q in enumerate(questions):

        qtype = moodle_type

        if len(q["answers"]) <= 1:
            qtype = "essay"
            stats["ESSAY"] += 1
        elif moodle_type == "multichoiceset":
            stats["MULTIPLE CHOICE SET"] += 1
        else:
            stats["MULTIPLE CHOICE"] += 1

        question = ET.SubElement(quiz, "question", type=qtype)

        name = ET.SubElement(question, "name")
        ET.SubElement(name, "text").text = f"Soal {i+1:02d}"

        qtext = ET.SubElement(question, "questiontext", format="html")
        text_el = ET.SubElement(qtext, "text")

        html = q["text"]

        # =========================
        # INSERT GAMBAR KE HTML
        # =========================
        for img in q["images"]:
            html += f'<br/><img src="@@PLUGINFILE@@/{img["name"]}"/>'

        text_el.text = f"<![CDATA[{html}]]>"

        # =========================
        # FILE GAMBAR
        # =========================
        for img in q["images"]:
            file_el = ET.SubElement(qtext, "file", name=img["name"], encoding="base64")
            file_el.text = img["data"]

        if qtype != "essay":
            single = ET.SubElement(question, "single")
            single.text = "false" if qtype == "multichoiceset" else "true"

            shuffle = ET.SubElement(question, "shuffleanswers")
            shuffle.text = "true"

            ans_num = ET.SubElement(question, "answernumbering")
            ans_num.text = "abc"

            for ans in q["answers"]:
                a = ET.SubElement(question, "answer", fraction="0", format="html")
                ET.SubElement(a, "text").text = f"<![CDATA[{ans}]]>"

    xml_str = ET.tostring(quiz, encoding="utf-8").decode("utf-8")

    return xml_str, stats, [], "Parsing selesai"
