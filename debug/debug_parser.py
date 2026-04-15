import re
from docx2python import docx2python


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip().upper()


def debug_docx(file):

    doc = docx2python(file)
    lines = [l.strip() for l in doc.text.split('\n') if l.strip()]

    logs = []

    logs.append("=== RAW ===")
    for i,l in enumerate(lines):
        logs.append(f"{i:03d} | {repr(l)}")

    logs.append("\n=== ANALYSIS ===")

    for i,l in enumerate(lines):

        if re.match(r'^\d+', l):
            logs.append(f"[SOAL] {l}")
            continue

        if re.match(r'^[A-Da-d]', l):
            logs.append(f"[OPSI] {l}")
            continue

        if normalize(l).startswith("ANS"):
            logs.append(f"[ANS] {l}")
            continue

        logs.append(f"[TEXT] {l}")

    return logs
