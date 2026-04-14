import re
import base64
import uuid
from docx import Document
import xml.etree.ElementTree as ET


# =========================
# DETEKSI SOAL (HANYA 1. 2. 3.)
# =========================
def is_question(text):
    text = text.strip()
    return re.match(r'^\d+\.\s+', text) is not None


# =========================
# DETEKSI OPSI (A. B. C. D.)
# =========================
def is_option(text):
    text = text.strip()
    return re.match(r'^[A-D][\.\)]\s*', text) is not None


# =========================
# AMBIL KUNCI JAWABAN
# =========================
def extract_answer_key(text):
    if "ANS:" in text.upper():
        ans = text.upper().split("ANS:")[1].strip()
        return [a.strip() for a in ans.split(",")]
    return []


# =========================
# IMAGE HANDLER (INLINE)
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

        return {
            "name": filename,
            "data": encoded
        }

    except Exception:
        return None


# =========================
# PARSER UTAMA
# =========================
def parse_docx_to_moodle(file, moodle_type="multichoice"):

    doc = Document(file)

    quiz = ET.Element("quiz")

    questions = []

    current_question = False
    current_text = ""
    current_answers = []
    current_images = []
    correct_answers = []

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    # =========================
    # LOOP PARAGRAPH
    # =========================
    for para in doc.paragraphs:

        text = para.text.strip()

        if not text:
            continue

        # =========================
        # OPSI (HARUS PALING ATAS)
        # =========================
        if is_option(text):
            if current_question:
                current_answers.append(text)
            continue

        # =========================
        # KUNCI JAWABAN
        # =========================
        if "ANS:" in text.upper():
            correct_answers = extract_answer_key(text)
            continue

        # =========================
        # SOAL BARU (FIX UTAMA)
        # =========================
        if is_question(text):

            if current_question:
                questions.append({
                    "text": current_text,
                    "answers": current_answers,
                    "images": current_images,
                    "correct": correct_answers
                })

            current_question = True
            current_text = text
            current_answers = []
            current_images = []
            correct_answers = []

            continue

        # =========================
        # TEKS LANJUTAN (TERMASUK 1) 2) dll)
        # =========================
        if current_question:
            current_text += "<br/>" + text

        # =========================
        # IMAGE INLINE
        # =========================
        for run in para.runs:
            img = extract_image_from_run(run)
            if img and current_question:
                current_images.append(img)

    # append terakhir
    if current_question:
        questions.append({
            "text": current_text,
            "answers": current_answers,
            "images": current_images,
            "correct": correct_answers
        })

    # =========================
    # BUILD XML
    # =========================
    for i, q in enumerate(questions):

        # tentukan tipe soal
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

        html = q["text"]

        # GAMBAR
        for img in q["images"]:
            html += f'<br/><img src="@@PLUGINFILE@@/{img["name"]}"/>'

        text_el.text = f"<![CDATA[{html}]]>"

        # FILE GAMBAR
        for img in q["images"]:
            file_el = ET.SubElement(qtext, "file", name=img["name"], encoding="base64")
            file_el.text = img["data"]

        # =========================
        # JAWABAN
        # =========================
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
