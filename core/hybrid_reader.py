import zipfile
from lxml import etree
from docx2python import docx2python
from utils.xml_parser import get_xml_info


def clean_text(text):
    return text.strip() if text else ""


def read_docx_hybrid(path):

    # ======================
    # XML PARSING (UTAMA)
    # ======================
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")

    root = etree.fromstring(xml)
    ns = root.nsmap

    elements = []

    for p in root.findall(".//w:p", namespaces=ns):

        text, level, has_drawing = get_xml_info(p, ns)
        text = clean_text(text)

        # 🔥 FILTER PARAGRAF KOSONG
        if not text and not has_drawing:
            continue

        elements.append({
            "text": text,
            "level": level,
            "has_drawing": has_drawing
        })

    # ======================
    # FALLBACK TEXT (AMAN)
    # ======================
    doc = docx2python(path)
    fallback_lines = [clean_text(l) for l in doc.text.split("\n") if clean_text(l)]

    # 🔥 SAFE MERGE (TIDAK PAKAI INDEX BUTA)
    fi = 0
    for el in elements:

        if not el["text"]:
            if fi < len(fallback_lines):
                el["text"] = fallback_lines[fi]
                fi += 1

    # ======================
    # DEBUG (OPSIONAL)
    # ======================
    # print untuk cek mismatch
    # for i, el in enumerate(elements):
    #     print(i, el["level"], el["text"])

    return elements
