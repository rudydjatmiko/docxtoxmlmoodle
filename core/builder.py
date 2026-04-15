from utils.text import wrap_arabic


def build_xml(questions, image_handler=None):

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']

    for i, q in enumerate(questions, start=1):

        xml.append('<question type="multichoice">')
        xml.append(f'<name><text>Soal {i:02d}</text></name>')

        # ===== TEXT =====
        xml.append('<questiontext format="html">')
        xml.append(f'<text><![CDATA[{wrap_arabic(q.text)}]]></text>')
        xml.append('</questiontext>')

        # ===== MODE =====
        is_multi = len(q.correct) > 1
        xml.append(f'<single>{"false" if is_multi else "true"}</single>')
        xml.append('<shuffleanswers>true</shuffleanswers>')
        xml.append('<answernumbering>abc</answernumbering>')

        # ===== OPTIONS =====
        for idx, opt in enumerate(q.options):
            label = chr(65 + idx)

            if is_multi:
                frac = 100 / len(q.correct) if label in q.correct else 0
            else:
                frac = 100 if label in q.correct else 0

            xml.append(f'<answer fraction="{frac}" format="html">')
            xml.append(f'<text><![CDATA[{wrap_arabic(opt)}]]></text>')
            xml.append('</answer>')

        xml.append('</question>')

    xml.append('</quiz>')

    return "\n".join(xml)
