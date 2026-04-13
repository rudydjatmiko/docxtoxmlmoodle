def build_mc(xml, stats, q_text, options, ans, q_num):

    # 🔥 DETEKSI JAWABAN BENAR (SUPER ROBUST)
    correct = re.findall(r'[A-D]', ans.upper())
    is_multi = len(correct) > 1

    # 🔥 TYPE SOAL
    if is_multi:
        xml += '<question type="multichoiceset">\n'
    else:
        xml += '<question type="multichoice">\n'

    xml += f'<name><text>Soal {q_num:02d}</text></name>\n'

    xml += '<questiontext format="html">\n'
    xml += f'<text><![CDATA[{wrap_arabic(q_text)}]]></text>\n'
    xml += '</questiontext>\n'

    # ❗ hanya untuk single choice
    if not is_multi:
        xml += '<single>true</single>\n'

    # 🔥 TAMBAHAN WAJIB (sesuai Moodle export)
    xml += '<shuffleanswers>true</shuffleanswers>\n'
    xml += '<answernumbering>abc</answernumbering>\n'

    # 🔥 ALL OR NOTHING (TANPA PARTIAL)
    for i, opt in enumerate(options):
        label = chr(65+i)

        if label in correct:
            frac = "100"
        else:
            frac = "0"

        xml += f'<answer fraction="{frac}" format="html">\n'
        xml += f'<text><![CDATA[{wrap_arabic(opt)}]]></text>\n'
        xml += '<feedback format="html"><text></text></feedback>\n'
        xml += '</answer>\n'

    xml += '</question>\n'

    # 🔥 STATISTIK
    if is_multi:
        stats["MULTIPLE CHOICE SET"] += 1
    else:
        stats["MULTIPLE CHOICE"] += 1

    return xml, stats
