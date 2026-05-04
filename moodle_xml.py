import xml.etree.ElementTree as ET
from docx import Document
import re
import base64

def to_moodle_xml(file):
    file.seek(0)
    doc = Document(file)
    root = ET.Element("quiz")
    
    # Menambahkan kategori kursus (sesuai sampel)
    cat_q = ET.SubElement(root, "question", type="category")
    cat = ET.SubElement(cat_q, "category")
    ET.SubElement(cat, "text").text = "$course$/Imported_Soal"

    questions = []
    temp_question = {"text": "", "options": [], "answer": ""}

    # Proses ekstraksi sederhana
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue

        if text.startswith("ANS:"):
            temp_question["answer"] = text.replace("ANS:", "").strip()
            questions.append(temp_question)
            temp_question = {"text": "", "options": [], "answer": ""}
        elif re.match(r'^[A-E][\.\)]', text) or len(temp_question["options"]) > 0 and len(text) < 50:
            # Seringkali pilihan jawaban tidak diawali huruf di docx Anda
            temp_question["options"].append(text)
        else:
            temp_question["text"] += " " + text

    for q in questions:
        question_el = ET.SubElement(root, "question", type="multichoice")
        
        # Name
        name = ET.SubElement(question_el, "name")
        ET.SubElement(name, "text").text = q["text"][:50].strip()

        # Question Text
        qtext = ET.SubElement(question_el, "questiontext", format="html")
        text_val = f"<![CDATA[<p>{q['text'].strip()}</p>]]>"
        ET.SubElement(qtext, "text").text = text_val

        # Cek Single atau Multiple Response (seperti ANS: A,C)
        is_single = "," not in q["answer"]
        ET.SubElement(question_el, "single").text = "true" if is_single else "false"
        
        # Mapping Jawaban
        correct_answers = [x.strip() for x in q["answer"].split(",")]
        labels = ["A", "B", "C", "D", "E"]
        
        for i, opt_text in enumerate(q["options"]):
            current_label = labels[i] if i < len(labels) else ""
            # Hitung skor: jika benar dan single (100), jika multiple (50), jika salah (0)
            if current_label in correct_answers:
                score = "100" if is_single else str(100 / len(correct_answers))
            else:
                score = "0"
            
            ans = ET.SubElement(question_el, "answer", fraction=score, format="html")
            ET.SubElement(ans, "text").text = f"<![CDATA[{opt_text}]]>"

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
