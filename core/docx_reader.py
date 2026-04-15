from docx import Document

def read_docx(path):
    doc = Document(path)
    elements = []

    for para in doc.paragraphs:
        elements.append({
            "type": "text",
            "text": para.text,
            "images": []
        })

        # detect image (inline)
        for run in para.runs:
            if "graphic" in run._element.xml:
                elements[-1]["images"].append(run._element.xml)

    return elements
