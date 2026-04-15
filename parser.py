from docx2python import docx2python

from core.parser_engine import parse_lines
from core.builder import build_xml
from utils.text import clean_lines


def parse_docx_to_moodle(file):

    logs = []

    file.seek(0)
    doc = docx2python(file)

    lines = clean_lines(doc.text)

    logs.append(f"Total lines: {len(lines)}")

    questions = parse_lines(lines, logs)

    logs.append(f"Detected questions: {len(questions)}")

    xml = build_xml(questions)

    stats = {
        "MULTIPLE CHOICE": len(questions),
        "MULTIPLE CHOICE SET": 0,
        "ESSAY": 0
    }

    return xml, stats, logs, "Converted (Refactored)"
