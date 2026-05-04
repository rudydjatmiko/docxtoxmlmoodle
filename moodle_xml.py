import xml.etree.ElementTree as ET
from docx import Document
import re

def to_moodle_xml(file):
    file.seek(0)
    doc = Document(file)
    root = ET.Element("quiz")
    
    questions = []
    current_q = None

    for para in doc.paragraphs:
        # Mengambil informasi level numbering
        ilvl = -1
        pPr = para._element.pPr
        if pPr is not None and pPr.numPr is not None:
            if pPr.numPr.ilvl is not None:
                ilvl = pPr.numPr.ilvl.val

        text = para.text.strip()
        
        # 1. DETEKSI NOMOR SOAL (Level 0)
        if ilvl == 0:
            if current_q:
                questions.append(current_q)
            current_q = {"text": text, "options": [], "ans": "", "type": "essay"}
            continue

        if current_q:
            # 2. DETEKSI PILIHAN JAWABAN (Level 1)
            if ilvl == 1:
                current_q["options"].append(text)
                # Jika ada pilihan, otomatis bukan essay
                current_q["type"] = "multichoice" 
            
            # 3. DETEKSI KUNCI JAWABAN (ANS:)
            elif text.upper().startswith("ANS:"):
                current_q["ans"] = text.split(":")[1].strip().upper()
                # Jika ANS mengandung koma, ubah ke All or Nothing
                if "," in current_q["ans"]:
                    current_q["type"] = "multichoiceset"
            
            # 4. TEKS TAMBAHAN (Instruksi atau bagian dari soal)
            elif text:
                current_q["text"] += "<br/>" + text

    # Tambahkan soal terakhir
    if current_q:
        questions.append(current_q)

    # --- KONSTRUKSI XML MOODLE ---
    for q in questions:
        q_el = ET.SubElement(root, "question", type=q["type"])
        
        # Nama Soal
        name = ET.SubElement(q_el, "name")
        ET.SubElement(name, "text").text = q["text"][:50].replace("<br/>", " ")
        
        # Teks Soal
        qtext = ET.SubElement(q_el, "questiontext", format="html")
        ET.SubElement(qtext, "text").text = f"<![CDATA[<p>{q['text']}</p>]]>"

        if q["type"] in ["multichoice", "multichoiceset"]:
            correct_list = [x.strip() for x in q["ans"].split(",")]
            ET.SubElement(q_el, "single").text = "true" if q["type"] == "multichoice" else "false"
            ET.SubElement(q_el, "answernumbering").text = "abc"
            
            # Moodle menggunakan urutan alfabet untuk pilihan
            labels = ["A", "B", "C", "D", "E"]
            for i, opt in enumerate(q["options"]):
                label = labels[i] if i < len(labels) else ""
                
                # Bobot nilai sesuai tipe soal
                fraction = "100" if label in correct_list else "0"
                
                ans_el = ET.SubElement(q_el, "answer", fraction=fraction, format="html")
                ET.SubElement(ans_el, "text").text = f"<![CDATA[{opt}]]>"

        elif q["type"] == "essay":
            ET.SubElement(q_el, "responseformat").text = "editor"
            ET.SubElement(q_el, "responserequired").text = "1"
            grader = ET.SubElement(q_el, "graderinfo", format="html")
            ET.SubElement(grader, "text").text = f"<![CDATA[<p>Kunci Jawaban: {q['ans']}</p>]]>"

    return ET.tostring(root, encoding="utf-8")
