def build_html(content):
    html = ""

    for el in content:
        if el["text"]:
            html += f"<p>{el['text']}</p>"

        for img in el["images"]:
            html += f'<img src="@@PLUGINFILE@@/{img["name"]}"/><br>'

    return html


def build_xml(questions):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']

    for i, q in enumerate(questions):

        if not q.choices:
            continue

        is_multi = len(q.answers) > 1

        xml.append('<question type="multichoice">')

        xml.append(f"<name><text>Question {i+1}</text></name>")

        html = build_html(q.content)

        xml.append('<questiontext format="html">')
        xml.append(f"<text><![CDATA[{html}]]></text>")

        for el in q.content:
            for img in el["images"]:
                xml.append(f'''
<file name="{img["name"]}" encoding="base64">
{img["data"]}
</file>
''')

        xml.append('</questiontext>')

        xml.append(f"<single>{'false' if is_multi else 'true'}</single>")
        xml.append("<shuffleanswers>true</shuffleanswers>")

        for c in q.choices:
            fraction = 100 if c["label"] in q.answers else 0

            xml.append(f'''
<answer fraction="{fraction}" format="html">
<text><![CDATA[{c["text"]}]]></text>
</answer>
''')

        xml.append('</question>')

    xml.append('</quiz>')
    return "\n".join(xml)
