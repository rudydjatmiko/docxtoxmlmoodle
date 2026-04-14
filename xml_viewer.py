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
# RENDER SOAL
# =========================
def render_question(q, idx):
    """
    Tampilkan 1 soal
    """

    st.markdown(f"### 📝 Soal {idx+1} ({q['type']})")

    if q["name"]:
        st.caption(q["name"])

    # tampilkan soal (HTML)
    if q["text"]:
        st.markdown(q["text"], unsafe_allow_html=True)

    # tampilkan gambar
    if q["images"]:
        for name, data in q["images"].items():
            try:
                img_bytes = base64.b64decode(data)
                st.image(img_bytes, caption=name)
            except:
                st.warning(f"Gagal decode gambar: {name}")

    # tampilkan jawaban
    if q["answers"]:
        st.markdown("**Pilihan Jawaban:**")

        for opt in q["answers"]:
            if opt in q["correct"]:
                st.markdown(f"✅ **{opt}**")
            else:
                st.markdown(f"• {opt}")

    st.divider()


# =========================
# RENDER SEMUA
# =========================
def render_all_questions(questions):
    """
    Render semua soal
    """

    st.success(f"Total soal: {len(questions)}")

    for i, q in enumerate(questions):
        render_question(q, i)
