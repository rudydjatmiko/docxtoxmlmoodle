import re
from docx2python import docx2python
from utils import wrap_arabic

# 🔥 IMPORT IMAGE HANDLER
from image_handler import (
    extract_images,
    replace_image_placeholder,
    append_images_to_xml
)


# =========================
# CONSTANT REGEX
# =========================
RE_QUESTION = re.compile(r'^\d+')
RE_OPTION = re.compile(r'^\(?([A-Da-d])[\.\)]')
RE_ANS = re.compile(r'\bANS\b', re.IGNORECASE)


# =========================
# NORMALIZE
# =========================
def normalize(text):
    return re.sub(r'\s+', '', text).upper()


# =========================
# PREPROCESS TEXT
# =========================
def preprocess_lines(lines):
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if normalize(line) == "MULTIPLE" and i + 1 < len(lines):
            if normalize(lines[i + 1]) == "CHOICE":
                result.append("MULTIPLECHOICE")
                i += 2
                continue

        if re.match(r'^[A-Da-d][\.\)]?$', line) and i + 1 < len(lines):
            result.append(line + " " + lines[i + 1])
            i += 2
            continue

        if re.match(r'^\d+[\.\)]?$', line) and i + 1 < len(lines):
            result.append(line + " " + lines[i + 1])
            i += 2
            continue

        result.append(line)
        i += 1

    return result


# =========================
# BUILD MULTICHOICE
# =========================
def build_mc(xml, stats, q_text, options, ans, q_num, images):

    # 🔥 REPLACE GAMBAR
    q_text = replace_image_placeholder(q_text, images)

    correct = re.findall(r'[A-D]', ans.upper())
    is_multi = len(correct) > 1

    qtype = "multichoiceset" if is_multi else "multichoice"

    xml.append(f'<question type="{qtype}">')
    xml.append(f'<name><text>Soal {q_num:02d}</text></name>')

    xml.append('<questiontext format="html">')
    xml.append(f'<text><![CDATA[{wrap_arabic(q_text)}]]></text>')
    xml.append('</questiontext>')

    if not is_multi:
        xml.append('<single>true</single>')

    xml.append('<shuffleanswers>true</shuffleanswers>')
    xml.append('<answernumbering>abc</answernumbering>')

    for i, opt in enumerate(options):
        label = chr(65 + i)
        frac = "100" if label in correct else "0"

        xml.append(f'<answer fraction="{frac}" format="html">')
        xml.append(f'<text><![CDATA[{wrap_arabic(opt)}]]></text>')
        xml.append('<feedback format="html"><text></text></feedback>')
        xml.append('</answer>')

    # 🔥 TAMBAHKAN GAMBAR KE XML
    append_images_to_xml(xml, images)

    xml.append('</question>')

    if is_multi:
        stats["MULTIPLE CHOICE SET"] += 1
    else:
        stats["MULTIPLE CHOICE"] += 1


# =========================
# BUILD ESSAY
# =========================
def build_essay(xml, stats, q_text, ans, q_num, images):

    q_text = replace_image_placeholder(q_text, images)

    xml.append('<question type="essay">')
    xml.append(f'<name><text>Soal {q_num:02d}</text></name>')

    xml.append('<questiontext format="html">')
    xml.append(f'<text><![CDATA[{wrap_arabic(q_text)}]]></text>')
    xml.append('</questiontext>')

    xml.append('<generalfeedback format="html">')
    xml.append(f'<text><![CDATA[{ans}]]></text>')
    xml.append('</generalfeedback>')

    # 🔥 TAMBAHKAN GAMBAR
    append_images_to_xml(xml, images)

    xml.append('</question>')

    stats["ESSAY"] += 1


# =========================
# MAIN PARSER
# =========================
def parse_docx_to_moodle(file):

    logs = []

    # ===== TEXT =====
    file.seek(0)  # 🔥 WAJIB
    doc = docx2python(file)

    lines = [l.strip() for l in doc.text.split('\n') if l.strip()]
    lines = preprocess_lines(lines)

    # ===== IMAGES =====
    file.seek(0)  # 🔥 WAJIB
    images = extract_images(file)
    file.seek(0)

    logs.append(f"[DEBUG] TOTAL IMAGES: {len(images)}")

    # ===== HEADER =====
    header = []
    i = 0
    while i < len(lines):
        if normalize(lines[i]) in ["MULTIPLECHOICE", "ESSAY"]:
            break
        header.append(lines[i])
        i += 1

    title = " - ".join(header)

    # ===== INIT =====
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

    # ===== LOOP =====
    while i < len(lines):

        line = lines[i]
        norm = normalize(line)

        if norm == "MULTIPLECHOICE":
            mode = "MC"
            i += 1
            continue

        if norm == "ESSAY":
            mode = "ESSAY"
            q_text = ""
            i += 1
            continue

        if RE_ANS.search(line):

            match = re.search(r'ANS\s*[:\-]?\s*(.*)', line, re.IGNORECASE)
            ans = match.group(1) if match else ""

            if mode == "ESSAY":
                build_essay(xml, stats, q_text, ans, q_num, images)
            else:
                build_mc(xml, stats, q_text, options, ans, q_num, images)

            q_num += 1
            q_text = ""
            options = []
            ans = ""

            i += 1
            continue

        if mode == "ESSAY":
            q_text += "<br/>" + line
            i += 1
            continue

        if RE_QUESTION.match(line):
            q_text = re.sub(r'^\d+[\.\)]?\s*', '', line)
            options = []
            ans = ""
            i += 1
            continue

        if RE_OPTION.match(line):
            opt = re.sub(r'^\(?[A-Da-d][\.\)]\s*', '', line)
            options.append(opt)
            i += 1
            continue

        if options:
            options[-1] += "<br/>" + line
        else:
            q_text += "<br/>" + line

        i += 1

    xml.append('</quiz>')

    return "\n".join(xml), stats, logs, title
