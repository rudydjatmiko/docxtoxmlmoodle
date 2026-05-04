import xml.etree.ElementTree as ET
from docx import Document
import re
from io import BytesIO

def to_moodle_xml(file):
    file.seek(0)
    doc = Document(file)
    root = ET.Element("quiz")
    
    current_question = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue

        # Deteksi Soal (Contoh: 1. Apa itu...)
        if re.match(r'^\d+[\.\)]', text):
            current_question = ET.SubElement(root, "question", type="multichoice")
            
            # Nama Soal
            name = ET.SubElement(current_question, "name")
            ET.SubElement(name, "text").text = text[:30] + "..."
            
            # Teks Soal
            qtext = ET.SubElement(current_question, "questiontext", format="html")
            ET.SubElement(qtext, "text").text = f"<![CDATA[<p>{text}</p>]]>"
            
            # Setting Default Moodle
            ET.SubElement(current_question, "single").text = "true"
            ET.SubElement(current_question, "answernumbering").text = "abc"
            ET.SubElement(current_question, "shuffleanswers").text = "1"

        # Deteksi Pilihan Jawaban (Contoh: A. Jawaban)
        elif re.match(r'^[A-E][\.\)]', text):
            if current_question is not None:
                # Cek jika ada bagian yang BOLD sebagai kunci jawaban
                is_correct = any(run.bold for run in para.runs)
                score = "100" if is_correct else "0"
                
                ans = ET.SubElement(current_question, "answer", fraction=score)
                atext = ET.SubElement(ans, "text")
                # Ambil teks setelah "A. "
                atext.text = re.sub(r'^[A-E][\.\)]\s*', '', text)
                
                feedback = ET.SubElement(ans, "feedback")
                ET.SubElement(feedback, "text").text = "Benar" if is_correct else "Salah"

    # Convert ke String XML
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
