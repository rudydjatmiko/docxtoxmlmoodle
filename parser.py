import re
from docx2python import docx2python
from utils import wrap_arabic

from image_handler import (
    extract_images,
    replace_image_placeholder,
    append_images_to_xml
)

# =========================
# REGEX
# =========================
RE_QUESTION = re.compile(r'^\d+')
RE_OPTION = re.compile(r'^\(?([A-Da-d])[\.\)]')
RE_ANS = re.compile(r'\bANS\b', re.IGNORECASE)


def normalize(text):
    return re.sub(r'\s+', '', text).upper()


# =========================
# MAIN PARSER
# =========================
def parse_docx_to_moodle(file, moodle_version="4.x"):

    logs = []

    # ===== READ TEXT =====
    file.seek(0)
    doc = docx2python(file)
    lines = [l.strip() for l in doc.text.split('\n') if l.strip()]

    # ===== READ IMAGES =====
    file.seek(0)
    image_map, image_data = extract_images(file)
    file.seek(0)

    logs.append(f"Images detected: {len(image_data)}")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    mode = "MC"
    q_text = ""
    options = []
    ans = ""
    q_num = 1

    i = 0

    # =========================
    # LOOP
    # =========================
    while i < len(lines):

        line = lines[i]
        norm = normalize(line)

        # ===== TIPE SOAL =====
        if norm == "MULTIPLECHOICE":
            mode = "MC"
            i += 1
            continue

        if norm == "ESSAY":
            mode = "ESSAY"
            q_text = ""
            i += 1
            continue

        # ===== JAWABAN =====
        if RE_ANS.search(line):

            match = re.search(r'ANS\s*[:\-]?\s*(.*)', line, re.IGNORECASE)
            ans = match.group(1) if match else ""

            if mode == "ESSAY":
                build_essay(
                    xml, stats, q_text, ans, q_num,
                    image_map, image_data
                )
            else:
                build_mc(
                    xml, stats, q_text, options, ans, q_num,
                    image_map, image_data, moodle_version
                )

            q_num += 1
            q_text = ""
            options = []
            ans = ""

            i += 1
            continue

        # ===== ESSAY =====
        if mode == "ESSAY":
            q_text += "<br/>" + line
            i += 1
            continue

        # ===== NOMOR SOAL =====
        if RE_QUESTION.match(line):
            q_text = re.sub(r'^\d+[\.\)]?\s*', '', line)
            options = []
            ans = ""
            i += 1
            continue

        # ===== OPSI =====
        if RE_OPTION.match(line):
            opt = re.sub(r'^\(?[A-Da-d][\.\)]\s*', '', line)
            options.append(opt)
            i += 1
            continue

        # ===== LANJUTAN =====
        if options:
            options[-1] += "<br/>" + line
        else:
            q_text += "<br/>" + line

        i += 1

    xml.append('</quiz>')

    return "\n".join(xml), stats, logs, "Converted"


# =========================
# BUILD MC
# =========================
def build_mc(xml, stats, q_text, options, ans, q_num,
             image_map, image_data, moodle_version):

    used_images = {}

    q_text = replace_image_placeholder(
        q_text, image_map, image_data, used_images
    )

    correct = re.findall(r'[A-D]', ans.upper())
    is_multi = len(correct) > 1

    # ===== TIPE SOAL =====
    if moodle_version.startswith("3"):
        qtype = "multichoiceset" if is_multi else "multichoice"
    else:
        qtype = "multichoice"

    xml.append(f'<question type="{qtype}">')
    xml.append(f'<name><text>Soal {q_num:02d}</text></name>')

    # ===== QUESTION TEXT =====
    xml.append('<questiontext format="html">')
    xml.append(f'<text><![CDATA[{wrap_arabic(q_text)}]]></text>')

    append_images_to_xml(xml, used_images)

    xml.append('</questiontext>')

    # ===== SINGLE / MULTI =====
    if is_multi:
        xml.append('<single>false</single>')
    else:
        xml.append('<single>true</single>')

    xml.append('<shuffleanswers>true</shuffleanswers>')
    xml.append('<answernumbering>abc</answernumbering>')

    # ===== FRACTION =====
    for i, opt in enumerate(options):
        label = chr(65 + i)

        if is_multi:
            frac = str(100 / len(correct)) if label in correct else "0"
        else:
            frac = "100" if label in correct else "0"

        xml.append(f'<answer fraction="{frac}" format="html">')
        xml.append(f'<text><![CDATA[{wrap_arabic(opt)}]]></text>')
        xml.append('</answer>')

    xml.append('</question>')

    if is_multi:
        stats["MULTIPLE CHOICE SET"] += 1
    else:
        stats["MULTIPLE CHOICE"] += 1


# =========================
# BUILD ESSAY
# =========================
def build_essay(xml, stats, q_text, ans, q_num,
                image_map, image_data):

    used_images = {}

    q_text = replace_image_placeholder(
        q_text, image_map, image_data, used_images
    )

    xml.append('<question type="essay">')
    xml.append(f'<name><text>Soal {q_num:02d}</text></name>')

    xml.append('<questiontext format="html">')
    xml.append(f'<text><![CDATA[{wrap_arabic(q_text)}]]></text>')

    append_images_to_xml(xml, used_images)

    xml.append('</questiontext>')

    xml.append('<generalfeedback format="html">')
    xml.append(f'<text><![CDATA[{ans}]]></text>')
    xml.append('</generalfeedback>')

    xml.append('</question>')

    stats["ESSAY"] += 1
