import xml.etree.ElementTree as ET
import base64
import streamlit as st


# =========================
# PARSE XML
# =========================
def parse_xml_questions(xml_content):
    """
    Parse XML Moodle → list of questions
    """

    root = ET.fromstring(xml_content)
    questions = []

    for q in root.findall("question"):

        qtype = q.attrib.get("type", "unknown")

        name = q.findtext("name/text", default="")

        qtext_elem = q.find("questiontext/text")
        qtext = qtext_elem.text if qtext_elem is not None else ""

        answers = []
        correct = []

        for ans in q.findall("answer"):
            text = ans.findtext("text", default="")
            fraction = ans.attrib.get("fraction", "0")

            answers.append(text)

            if fraction == "100":
                correct.append(text)

        # 🔥 ambil gambar
        images = {}
        for file in q.findall(".//file"):
            fname = file.attrib.get("name")
            data = file.text

            if fname and data:
                images[fname] = data

        questions.append({
            "type": qtype,
            "name": name,
            "text": qtext,
            "answers": answers,
            "correct": correct,
            "images": images
        })

    return questions


# =========================
# 🔥 INLINE IMAGE FIX
# =========================
def inject_base64_to_html(text, images):
    """
    Ganti @@PLUGINFILE@@ → base64 inline
    supaya gambar muncul di posisi yang benar
    """

    if not text:
        return text

    for name, data in images.items():

        # default jpeg (aman)
        base64_src = f"data:image/jpeg;base64,{data}"

        text = text.replace(
            f"@@PLUGINFILE@@/{name}",
            base64_src
        )

    return text


# =========================
# RENDER 1 SOAL
# =========================
def render_question(q, idx):

    st.markdown(f"### 📝 Soal {idx+1} ({q['type']})")

    if q["name"]:
        st.caption(q["name"])

    # 🔥 inject image ke HTML
    html = inject_base64_to_html(q["text"], q["images"])

    # tampilkan soal + gambar INLINE
    if html:
        st.markdown(html, unsafe_allow_html=True)

    # =========================
    # PILIHAN JAWABAN
    # =========================
    if q["answers"]:
        st.markdown("**Pilihan Jawaban:**")

        for opt in q["answers"]:
            if opt in q["correct"]:
                st.markdown(f"✅ **{opt}**")
            else:
                st.markdown(f"• {opt}")

    st.divider()


# =========================
# RENDER SEMUA SOAL
# =========================
def render_all_questions(questions):

    st.success(f"Total soal: {len(questions)}")

    for i, q in enumerate(questions):
        render_question(q, i)
