import re
from docx2python import docx2python
from utils import wrap_arabic


# =========================
# NORMALIZE
# =========================
def normalize(text):
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')
    text = text.replace('\t', ' ')
    text = re.sub(r'\s+', '', text)
    return text.upper()


# =========================
# PREPROCESS (FIX SPLIT)
# =========================
def preprocess_lines(lines):
    fixed = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        norm = normalize(line)

        # MULTIPLE + CHOICE
        if norm == "MULTIPLE" and i + 1 < len(lines):
            if normalize(lines[i+1]) == "CHOICE":
                fixed.append("MULTIPLECHOICE")
                i += 2
                continue

        # opsi split (a. + next line)
        if re.match(r'^[A-Da-d][\.\)]?$', line) and i + 1 < len(lines):
            fixed.append(line + " " + lines[i+1])
            i += 2
            continue

        # nomor split (1. + next line)
        if re.match(r'^\d+[\.\)]?$', line) and i + 1 < len(lines):
            fixed.append(line + " " + lines[i+1])
            i += 2
            continue

        fixed.append(line)
        i += 1

    return fixed


# =========================
# DETECT MODE
# =========================
def detect_mode(line):
    norm = normalize(line)

    if norm == "MULTIPLECHOICE":
        return "MC"
    elif norm == "ESSAY":
        return "ESSAY"
    return None


# =========================
# BUILD MC
# =========================
def build_mc(xml, stats, q_text, options, ans, q_num):

    correct = [x.strip().upper() for x in ans.split(",") if x.strip()]
    is_multi = len(correct) > 1

    xml += f'<question type="multichoice">\n'
    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'
    xml += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(q_text)}]]></text></questiontext>\n'
    xml += f'<single>{"false" if is_multi else "true"}</single>\n'

    for i, opt in enumerate(options):
        label = chr(65 + i)
        frac = "100" if label in correct else "0"

        if is_multi and label in correct:
            frac = str(round(100/len(correct), 5))

        xml += f'<answer fraction="{frac}">\n'
        xml += f'<text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
        xml += '</answer>\n'

    xml += '</question>\n'

    if is_multi:
        stats["MULTIPLE CHOICE SET"] += 1
    else:
        stats["MULTIPLE CHOICE"] += 1

    return xml, stats


# =========================
# BUILD ESSAY
# =========================
def build_essay(xml, stats, q_text, ans, q_num):

    xml += f'<question type="essay">\n'
    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'
    xml += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(q_text)}]]></text></questiontext>\n'

    if ans:
        xml += f'<generalfeedback><text><![CDATA[{ans}]]></text></generalfeedback>\n'

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
        if detect_mode(raw_lines[i]):
            break
        header.append(raw_lines[i])
        i += 1

    title = " - ".join(header)

    # INIT
    xml = '<?xml version="1.0"?><quiz>\n'
    stats = {"MULTIPLE CHOICE":0,"MULTIPLE CHOICE SET":0,"ESSAY":0}

    mode = None
    q_text = ""
    options = []
    ans = ""
    q_num = 1

    while i < len(raw_lines):

        line = raw_lines[i]

        # MODE
        m = detect_mode(line)
        if m:
            mode = m
            i += 1
            continue

        # SOAL
        match_q = re.match(r'^\d+', line)
        if match_q:
            q_text = re.sub(r'^\d+[\.\)]?\s*','',line)
            options = []
            ans = ""
            i += 1
            continue

        # OPSI
        match_opt = re.match(r'^\(?([A-Da-d])[\.\)]?\s*(.*)', line)
        if match_opt:
            options.append(match_opt.group(2))
            i += 1
            continue

        # ANS
        if normalize(line).startswith("ANS"):

            if mode == "MC":
                match = re.search(r'ANS[:\-]?\s*(.*)', line)
                ans = match.group(1) if match else ""
                xml, stats = build_mc(xml, stats, q_text, options, ans, q_num)
            else:
                match = re.search(r'ANS[:\-]?\s*(.*)', line)
                ans = match.group(1) if match else ""
                xml, stats = build_essay(xml, stats, q_text, ans, q_num)

            q_num += 1
            q_text = ""
            options = []
            ans = ""
            i += 1
            continue

        # lanjutan
        if options:
            options[-1] += "<br/>" + line
        else:
            q_text += "<br/>" + line

        i += 1

    xml += '</quiz>'

    return xml, stats, [], title
