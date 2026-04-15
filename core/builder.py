def build_html(lines):
    return "<br/>".join(lines)


def build_xml(questions):

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']

    for q in questions:

        q_text = build_html(q["question"])

        # ======================
        # MC
        # ======================
        if q["type"] == "MC" and q["choices"]:

            is_multi = len(q["answers"]) > 1

            xml.append('<question type="multichoice">')
            xml.append(f"<name><text>Question {q['number']}</text></name>")

            xml.append('<questiontext format="html">')
            xml.append(f"<text><![CDATA[{q_text}]]></text>")
            xml.append('</questiontext>')

            xml.append(f"<single>{'false' if is_multi else 'true'}</single>")
            xml.append("<shuffleanswers>true</shuffleanswers>")

            total_correct = len(q["answers"]) if is_multi else 1

            for c in q["choices"]:

                if c["label"] in q["answers"]:
                    fraction = 100 / total_correct
                else:
                    fraction = 0

                xml.append(f"""
<answer fraction="{fraction}" format="html">
<text><![CDATA[{c["text"]}]]></text>
</answer>
""")

            xml.append('</question>')

        # ======================
        # ESSAY
        # ======================
        elif q["type"] == "ESSAY":

            xml.append('<question type="essay">')
            xml.append(f"<name><text>Question {q['number']}</text></name>")

            xml.append('<questiontext format="html">')
            xml.append(f"<text><![CDATA[{q_text}]]></text>")
            xml.append('</questiontext>')

            xml.append('</question>')

    xml.append('</quiz>')

    return "\n".join(xml)
