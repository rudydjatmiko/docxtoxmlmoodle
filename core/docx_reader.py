from docx import Document
from processors.image_handler import get_image_map, extract_images_from_paragraph

def read_docx(path):
    doc = Document(path)

    image_map = get_image_map(doc)

    elements = []

    for para in doc.paragraphs:
        images = extract_images_from_paragraph(para, image_map)

        elements.append({
            "type": "text",
            "text": para.text,
            "images": images
        })

    return elements
