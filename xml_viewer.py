import xml.etree.ElementTree as ET
import streamlit as st


def get_question_label(qtype):
    if qtype == "multichoice":
        return "📝 Multiple Choice"
    elif qtype == "multichoiceset":
        return "✅ All or Nothing"
    elif qtype == "essay":
        return "✍️ Essay"
    else:
        return f"❓ {qtype}"


def parse_xml_questions(xml_content):

    root = ET.fromstring(xml_content)
    questions = []

    for q in root.findall("question"):

        qtype = q.attrib.get("type")

        name = q.find("name/text").text

        qtext_el = q.find("questiontext/text")
        qtext = qtext_el.text if qtext_el is not None else ""

        answers = []
        for ans in q.findall("answer"):
            answers.append(ans.find("text").text)

        questions.append({
            "name": name,
            "type": qtype,
            "text": qtext,
            "answers": answers
        })

    return questions


def render_all_questions(questions):

    for q in questions:

        label = get_question_label(q["type"])

        st.markdown(f"### {q['name']} — {label}")

        st.markdown(q["text"], unsafe_allow_html=True)

        for a in q["answers"]:
            st.markdown(f"- {a}")

        st.markdown("---")
