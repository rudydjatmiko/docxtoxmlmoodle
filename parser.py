import re
from docx2python import docx2python
from utils import wrap_arabic


# =========================
# NORMALIZE
# =========================
def normalize(text):
    return re.sub(r'\s+', '', text).upper()


# =========================
# PREPROCESS (FIX SPLIT WORD)
# =========================
def preprocess_lines(lines):
    fixed = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # MULTIPLE + CHOICE (terpisah)
        if normalize(line) == "MULTIPLE" and i + 1 < len(lines):
            if normalize(lines[i + 1]) == "CHOICE":
                fixed.append("MULTIPLECHOICE")
                i += 2
                continue

        # opsi terpisah (a. + next line)
        if re.match(r'^[A-Da-d][\.\)]?$', line) and i + 1 < len(lines):
            fixed.append(line + " " + lines[i + 1])
            i += 2
            continue

        # nomor terpisah (1. + next line)
        if re.match(r'^\d+[\.\)]?$', line) and i + 1 < len(lines):
            fixed.append(line + " " + lines[i + 1])
            i += 2
            continue

        fixed.append(line)
        i += 1

    return fixed


# =========================
# BUILD MC / MC SET
# =========================
def build_mc(xml, stats, q_text, options, ans, q_num):

    # 🔥 SUPER ROBUST ANSWER PARSER
    correct = re.findall(r'[A-D]', ans.upper())
    is_multi = len(correct) > 1

    # 🔥 TYPE
    if is_multi:
        xml += '<question type="multichoiceset">\n'
    else:
        xml += '<question type="multichoice">\n'

    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'

    xml += '<questiontext format="html">\n'
    xml += f'<text><![CDATA[{wrap_arabic(q_text)}]]></text>\n'
    xml += '</questiontext>\n'

    # hanya untuk single choice
    if not is_multi:
        xml += '<single>true</single>\n'

    # standar Moodle
    xml += '<shuffleanswers>true</shuffleanswers>\n'
    xml += '<answernumbering>abc</answernumbering>\n'

    # 🔥 ALL OR NOTHING (100 / 0)
    for i, opt in enumerate(options):
        label = chr(65 + i)

        if label in correct:
            frac = "100"
        else:
            frac = "0"

        xml += f'<answer fraction="{frac}" format="html">\n'
        xml += f'<text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
        xml += '<feedback format="html"><text></text></feedback>\n'
        xml += '</answer>\n'

    xml += '</question>\n'

    # statistik
    if is_multi:
        stats["MULTIPLE CHOICE SET"] += 1
    else:
        stats["MULTIPLE CHOICE"] += 1

    return xml, stats


# =========================
# BUILD ESSAY
# =========================
def build_essay(xml, stats, q_text, ans, q_num):

    xml += '<question type="essay">\n'
    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'

    xml += '<questiontext format="html">\n'
    xml += f'<text><![CDATA[{wrap_arabic(q_text)}]]></text>\n'
    xml += '</questiontext>\n'

    xml += '<generalfeedback format="html">\n'
    xml += f'<text><![CDATA[{ans}]]></text>\n'
    xml += '</generalfeedback>\n'

    xml += '</question>\n'

    stats["ESSAY"] += 1
    return xml, stats


# =========================
# MAIN PARSER
# =========================
def parse_docx_to_moodle(file):

    doc = docx2python(file)
    raw_lines = [l.strip() for l in doc.text.split('\n') if l.strip()]
    raw_lines = preprocess_lines(raw_lines)

    # HEADER
    header = []
    i = 0
    while i < len(raw_lines):
        if normalize(raw_lines[i]) in ["MULTIPLECHOICE", "ESSAY"]:
            break
        header.append(raw_lines[i])
        i += 1

    title = " - ".join(header)

    # INIT
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    q_text = ""
    options = []
    ans = ""
    q_num = 1
    mode = "MC"

    # LOOP
    while i < len(raw_lines):

        line = raw_lines[i]

        # MODE SWITCH
        if normalize(line) == "MULTIPLECHOICE":
            mode = "MC"
            i += 1
            continue

        if normalize(line) == "ESSAY":
            mode = "ESSAY"
            q_text = ""
            i += 1
            continue

        # ===== ANS (FINALIZE) =====
        if re.search(r'\bANS\b', line, re.IGNORECASE):

            match = re.search(r'ANS\s*[:\-]?\s*(.*)', line, re.IGNORECASE)
            ans = match.group(1) if match else ""

            if mode == "ESSAY":
                xml, stats = build_essay(xml, stats, q_text, ans, q_num)
            else:
                xml, stats = build_mc(xml, stats, q_text, options, ans, q_num)

            q_num += 1
            q_text = ""
            options = []
            ans = ""

            i += 1
            continue

        # ===== ESSAY MODE =====
        if mode == "ESSAY":
            q_text += "<br/>" + line
            i += 1
            continue

        # ===== SOAL =====
        if re.match(r'^\d+', line):
            q_text = re.sub(r'^\d+[\.\)]?\s*', '', line)
            options = []
            ans = ""
            i += 1
            continue

        # ===== OPSI =====
        if re.match(r'^\(?[A-Da-d][\.\)]', line):
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

    xml += '</quiz>'

    return xml, stats, [], title
