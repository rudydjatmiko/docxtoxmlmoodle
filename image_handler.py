import base64
from docx import Document


def extract_images(docx_file):
    """
    Extract semua gambar dari docx → dict {filename: base64}
    """

    docx_file.seek(0)  # 🔥 WAJIB

    doc = Document(docx_file)
    images = {}
    index = 1

    for rel in doc.part._rels.values():

        if hasattr(rel, "target_part") and "image" in rel.target_ref:

            image_bytes = rel.target_part.blob
            filename = f"image{index}.png"

            encoded = base64.b64encode(image_bytes).decode()
            images[filename] = encoded

            index += 1

    return images


def replace_image_placeholder(text, image_map):
    """
    Ganti placeholder ----media/imageX.png----
    menjadi <img Moodle>
    """
    for i, name in enumerate(image_map.keys(), start=1):
        placeholder = f"----media/image{i}.png----"
        img_tag = f'<img src="@@PLUGINFILE@@/{name}" />'

        text = text.replace(placeholder, img_tag)

    return text


def append_images_to_xml(xml, image_map):
    """
    Tambahkan file base64 ke XML Moodle
    """
    for name, data in image_map.items():
        xml.append(
            f'<file name="{name}" encoding="base64">{data}</file>'
        )
