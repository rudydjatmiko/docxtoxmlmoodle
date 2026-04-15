def get_xml_info(paragraph):
    p = paragraph._element

    # ======================
    # NUMBERING (w:numPr)
    # ======================
    numPr = p.find('.//w:numPr', namespaces=p.nsmap)

    numbering = None
    if numPr is not None:
        ilvl = numPr.find('.//w:ilvl', namespaces=p.nsmap)
        numId = numPr.find('.//w:numId', namespaces=p.nsmap)

        numbering = {
            "level": int(ilvl.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')) if ilvl is not None else None,
            "numId": numId.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if numId is not None else None
        }

    # ======================
    # DRAWING (w:drawing)
    # ======================
    has_drawing = bool(p.xpath('.//w:drawing'))

    return numbering, has_drawing
