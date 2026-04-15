import zipfile
from lxml import etree
from docx2python import docx2python
from utils.xml_parser import get_xml_info

def read_docx_hybrid(path):

    # ===== XML =====
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")

    root = etree.fromstring(xml)
    ns = root.nsmap

    elements = []

    for p in root.findall(".//w:p", namespaces=ns):

        text, level, has_drawing = get_xml_info(p, ns)

        elements.append({
            "text": text,
            "level": level,
            "has_drawing": has_drawing
        })

    # ===== FALLBACK TEXT =====
    doc = docx2python(path)
    fallback_lines = [l.strip() for l in doc.text.split("\n") if l.strip()]

    # isi text kosong pakai fallback
    fi = 0
    for el in elements:
        if not el["text"] and fi < len(fallback_lines):
            el["text"] = fallback_lines[fi]
            fi += 1

    return elements
