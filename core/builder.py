def build_html(elements):
    html = ""

    for el in elements:

        text = el.get("text", "")
        images = el.get("images", [])

        if text:
            html += f"<p>{text}</p>"

        for img in images:
            html += f'<p><img src="@@PLUGINFILE@@/{img["name"]}" style="max-width:100%;height:auto;"></p>'

    return html


def build_xml(questions):

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']

    for i, q in enumerate(questions):

        if not q.choices:
            continue

        is_multi = len(q.answers) > 1

        xml.append('<question type="multichoice">')

        # ======================
        # NAME
        # ======================
        xml.append(f"<name><text>Question {i+1}</text></name>")

        # ======================
        # QUESTION TEXT (FIX DI SINI)
        # ======================
        html = build_html(q.question_text)

        xml.append('<questiontext format="html">')
        xml.append(f"<text><![CDATA[{html}]]></text>")

        # ======================
        # EMBED FILE (GAMBAR)
        # ======================
        for el in q.question_text:
            for img in el.get("images", []):
                xml.append(f'''
<file name="{img["name"]}" encoding="base64">
{img["data"]}
</file>
''')

        xml.append('</questiontext>')

        # ======================
        # TYPE
        # ======================
        xml.append(f"<single>{'false' if is_multi else 'true'}</single>")
        xml.append("<shuffleanswers>true</shuffleanswers>")

        # ======================
        # ANSWERS
        # ======================
        for c in q.choices:

            text = c.get("text", "")
            images = c.get("images", [])

            html_choice = f"<p>{text}</p>"

            for img in images:
                html_choice += f'<p><img src="@@PLUGINFILE@@/{img["name"]}"></p>'

            fraction = 100 if c["label"] in q.answers else 0

            xml.append(f'''
<answer fraction="{fraction}" format="html">
<text><![CDATA[{html_choice}]]></text>
</answer>
''')

        xml.append('</question>')

    xml.append('</quiz>')

    return "\n".join(xml)
