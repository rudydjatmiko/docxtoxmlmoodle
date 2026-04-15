def build_xml(questions):

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']

    for i, q in enumerate(questions):

        if not q["choices"]:
            continue

        is_multi = len(q["answers"]) > 1

        xml.append('<question type="multichoice">')

        xml.append(f"<name><text>Question {i+1}</text></name>")

        # ===== QUESTION TEXT =====
        q_html = "<br/>".join(q["question"])

        xml.append('<questiontext format="html">')
        xml.append(f"<text><![CDATA[{q_html}]]></text>")
        xml.append('</questiontext>')

        xml.append(f"<single>{'false' if is_multi else 'true'}</single>")
        xml.append("<shuffleanswers>true</shuffleanswers>")

        # ===== ANSWERS =====
        for idx, choice in enumerate(q["choices"]):

            label = chr(65 + idx)
            fraction = 100 if label in q["answers"] else 0

            xml.append(f'''
<answer fraction="{fraction}" format="html">
<text><![CDATA[{choice}]]></text>
</answer>
''')

        xml.append('</question>')

    xml.append('</quiz>')

    return "\n".join(xml)
