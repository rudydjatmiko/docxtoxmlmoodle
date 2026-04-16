import zipfile
from lxml import etree
from docx import Document
from docx2python import docx2python
from utils.xml_parser import get_xml_info


def clean(text):
    return text.strip() if text else ""


def read_docx_hybrid(path):

    # ======================
    # 1. XML (STRUCTURE)
    # ======================
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")

    root = etree.fromstring(xml)
    ns = root.nsmap

    xml_data = []
    for p in root.findall(".//w:p", namespaces=ns):
        text, level, has_drawing = get_xml_info(p, ns)

        xml_data.append({
            "xml_text": clean(text),
            "level": level,
            "has_drawing": has_drawing
        })

    # ======================
    # 2. python-docx (MAIN TEXT)
    # ======================
    doc = Document(path)
    pdoc_lines = [clean(p.text) for p in doc.paragraphs if clean(p.text)]

    # ======================
    # 3. docx2python (FALLBACK)
    # ======================
    doc2 = docx2python(path)
    fallback_lines = [clean(l) for l in doc2.text.split("\n") if clean(l)]

    # ======================
    # 4. MERGE SMART
    # ======================
    merged = []
    i1 = i2 = 0

    for el in xml_data:

        text = el["xml_text"]

        if i1 < len(pdoc_lines):
            text = pdoc_lines[i1]
            i1 += 1
        elif i2 < len(fallback_lines):
            text = fallback_lines[i2]
            i2 += 1

        if not text:
            continue

        merged.append({
            "text": text,
            "level": el["level"],
            "has_drawing": el["has_drawing"]
        })

    return merged
