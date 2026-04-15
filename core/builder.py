def build_html(lines):
    return "<br/>".join(lines)


def build_xml(questions):

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']

    for q in questions:

        q_text = build_html(q["question"])

        # ======================
        # MULTIPLE CHOICE
        # ======================
        if q["type"] == "MC":

            if not q["choices"]:
                continue

            is_multi = len(q["answers"]) > 1

            xml.append('<question type="multichoice">')

            # NAME
            xml.append(f"<name><text>Question {q['number']}</text></name>")

            # QUESTION TEXT
            xml.append('<questiontext format="html">')
            xml.append(f"<text><![CDATA[{q_text}]]></text>")
            xml.append('</questiontext>')

            # SETTINGS
            xml.append(f"<single>{'false' if is_multi else 'true'}</single>")
            xml.append("<shuffleanswers>true</shuffleanswers>")

            # ======================
            # ANSWERS
            # ======================
            total_correct = len(q["answers"]) if is_multi else 1

            for c in q["choices"]:

                label = c["label"]
                text = c["text"]

                if label in q["answers"]:
                    fraction = 100 / total_correct
                else:
                    fraction = 0

                xml.append(f"""
<answer fraction="{fraction}" format="html">
<text><![CDATA[{text}]]></text>
</answer>
""")

            xml.append('</question>')

        # ======================
        # ESSAY
        # ======================
        elif q["type"] == "ESSAY":

            xml.append('<question type="essay">')

            # NAME
            xml.append(f"<name><text>Question {q['number']}</text></name>")

            # QUESTION TEXT
            xml.append('<questiontext format="html">')
            xml.append(f"<text><![CDATA[{q_text}]]></text>")
            xml.append('</questiontext>')

            # OPTIONAL: jawabannya (jika ada)
            if q["answers"]:
                ans_text = "<br/>".join(q["answers"])

                xml.append(f"""
<generalfeedback format="html">
<text><![CDATA[{ans_text}]]></text>
</generalfeedback>
""")

            xml.append('</question>')

    xml.append('</quiz>')

    return "\n".join(xml)
