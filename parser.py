import re
from docx2python import docx2python
from utils import wrap_arabic


# =========================
# NORMALIZE (NO SPACE)
# =========================
def normalize(text):
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')
    text = text.replace('\t', ' ')
    text = re.sub(r'\s+', '', text)  # 🔥 hilangkan semua spasi
    return text.upper()


# =========================
# PREPROCESS (FIX WORD SPLIT)
# =========================
def preprocess_lines(raw_lines):
    fixed = []
    i = 0

    while i < len(raw_lines):
        line = raw_lines[i].strip()
        norm = normalize(line)

        # ===== FIX MULTIPLE + CHOICE =====
        if norm == "MULTIPLE" and i + 1 < len(raw_lines):
            next_norm = normalize(raw_lines[i + 1])
            if next_norm == "CHOICE":
                fixed.append("MULTIPLECHOICE")
                i += 2
                continue

        # ===== FIX OPSI SPLIT =====
        if re.match(r'^[A-Da-d][\.\)]?$', line) and i + 1 < len(raw_lines):
            merged = line + " " + raw_lines[i + 1]
            fixed.append(merged)
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
def build_mc(xml, stats, logs, q_text, options, ans, q_num):

    correct = [x.strip().upper() for x in ans.split(",") if x.strip()]
    correct = list(dict.fromkeys(correct))

    is_multi = len(correct) > 1

    xml += f'<question type="multichoice">\n'
    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'
    xml += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(q_text)}]]></text></questiontext>\n'
    xml += f'<single>{"false" if is_multi else "true"}</single>\n'

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

    logs.append(f"✅ Soal {q_num:02d} (MC)")
    return xml, stats, logs


# =========================
# BUILD ESSAY
# =========================
def build_essay(xml, stats, logs, q_text, ans, q_num):

    xml += f'<question type="essay">\n'
    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'
    xml += f'<questiontext format="html"><text><![CDATA[{wrap_arabic(q_text)}]]></text></questiontext>\n'

    if ans and ans.strip() != "---":
        xml += f'<generalfeedback format="html">\n'
        xml += f'<text><![CDATA[{wrap_arabic(ans)}]]></text>\n'
        xml += f'</generalfeedback>\n'

    xml += '</question>\n'

    stats["ESSAY"] += 1
    logs.append(f"✅ Soal {q_num:02d} (Essay)")
    return xml, stats, logs


# =========================
# MAIN PARSER
# =========================
def parse_docx_to_moodle(docx_file):

    try:
        doc = docx2python(docx_file)
        raw_text = doc.text

        raw_lines = [
            line.strip()
            for line in raw_text.split('\n')
            if line.strip()
        ]

        # 🔥 FIX STRUCTURE WORD
        raw_lines = preprocess_lines(raw_lines)

    except Exception as e:
        return None, {}, [], f"Error membaca file: {str(e)}"

    if len(raw_lines) < 3:
        return None, {}, [], "Dokumen tidak valid."

    # ================= HEADER =================
    header_lines = []
    i = 0

    while i < len(raw_lines):
        if detect_mode(raw_lines[i]):
            break
        header_lines.append(raw_lines[i])
        i += 1

    judul_paket = " - ".join(header_lines)

    # ================= INIT =================
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'

    stats = {
        "MULTIPLE CHOICE": 0,
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    logs = []

    mode = None
    q_text = ""
    options = []
    ans = ""
    q_num = 1

    # ================= LOOP =================
    while i < len(raw_lines):

        line = raw_lines[i]

        # ===== MODE =====
        new_mode = detect_mode(line)
        if new_mode:
            mode = new_mode
            i += 1
            continue

        # ===== NOMOR SOAL =====
        match_q = re.match(r'^(\d+)[.\s]+(.*)', line)
        if match_q:
            q_text = match_q.group(2)
            options = []
            ans = ""
            i += 1
            continue

        # ===== OPSI =====
        match_opt = re.match(r'^\(?([A-Da-d])[\.\)\s]+(.*)', line)
        if match_opt:
            options.append(match_opt.group(2))
            i += 1
            continue

        # ===== ANS (FINALIZE) =====
        if normalize(line).startswith("ANS"):

            if mode == "MC":
                match = re.search(r'ANS\s*[:\-]?\s*([A-Da-d,\s]+)', line)
                ans = match.group(1).upper() if match else ""
                xml, stats, logs = build_mc(xml, stats, logs, q_text, options, ans, q_num)
            else:
                match = re.search(r'ANS\s*[:\-]?\s*(.*)', line)
                ans = match.group(1) if match else ""
                xml, stats, logs = build_essay(xml, stats, logs, q_text, ans, q_num)

            q_num += 1
            q_text = ""
            options = []
            ans = ""

            i += 1
            continue

        # ===== LANJUTAN =====
        if options:
            options[-1] += "<br/>" + line
        else:
            q_text += "<br/>" + line

        i += 1

    xml += '</quiz>'

    return xml, stats, logs, judul_paket
