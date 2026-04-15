def get_xml_info(p, ns):
    # ===== TEXT =====
    texts = p.findall(".//w:t", namespaces=ns)
    text = "".join([t.text for t in texts if t.text]).strip()

    # ===== NUMBERING =====
    numPr = p.find('.//w:numPr', namespaces=ns)
    level = None

    if numPr is not None:
        ilvl = numPr.find('.//w:ilvl', namespaces=ns)
        if ilvl is not None:
            level = int(ilvl.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'))

    # ===== DRAWING =====
    has_drawing = bool(p.findall(".//w:drawing", namespaces=ns))

    return text, level, has_drawing
