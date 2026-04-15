from docx import Document
from processors.image_handler import get_image_map, extract_images_from_paragraph
from utils.xml_parser import get_xml_info

def read_docx(path):
    doc = Document(path)

    image_map = get_image_map(doc)
    elements = []

    for para in doc.paragraphs:

        numbering, has_drawing = get_xml_info(para)
        images = extract_images_from_paragraph(para, image_map)

        elements.append({
            "text": para.text,
            "images": images,
            "numbering": numbering,
            "has_drawing": has_drawing
        })

    return elements
