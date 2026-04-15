def build_html(content):
    html = ""

    for el in content:
        if el["text"]:
            html += f"<p>{el['text']}</p>"

        for img in el["images"]:
            html += f'<img src="@@PLUGINFILE@@/{img["name"]}"/><br>'

    return html


def build_xml(questions):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<quiz>')

    for i, q in enumerate(questions):

        is_multi = len(q.answers) > 1

        xml.append('<question type="multichoice">')

        # NAME
        xml.append("<name>")
        xml.append(f"<text>Question {i+1}</text>")
        xml.append("</name>")

        # QUESTION TEXT
        xml.append('<questiontext format="html">')

        html = build_html(q.content)

        xml.append(f"<text><![CDATA[{html}]]></text>")

        # embed images
        for el in q.content:
            for img in el["images"]:
                xml.append(f'''
                <file name="{img["name"]}" encoding="base64">
                {img["data"]}
                </file>
                ''')

        xml.append("</questiontext>")

        # SETTINGS
        xml.append(f"<single>{'false' if is_multi else 'true'}</single>")
        xml.append("<shuffleanswers>true</shuffleanswers>")

        # ANSWERS
        for c in q.choices:
            if c["label"] in q.answers:
                fraction = 100
            else:
                fraction = 0

            xml.append(f'''
            <answer fraction="{fraction}" format="html">
                <text><![CDATA[{c["text"]}]]></text>
            </answer>
            ''')

        xml.append("</question>")

    xml.append("</quiz>")

    return "\n".join(xml)
