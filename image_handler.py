import base64
from docx import Document
from PIL import Image
from io import BytesIO
import hashlib


def extract_images(docx_file):
    """
    Extract + compress + deduplicate image
    return:
        image_map: {index: filename}
        image_data: {filename: base64}
    """

    docx_file.seek(0)
    doc = Document(docx_file)

    image_map = {}
    image_data = {}
    hash_map = {}

    index = 1

    for rel in doc.part._rels.values():

        if hasattr(rel, "target_part") and "image" in rel.target_ref:

            try:
                image_bytes = rel.target_part.blob

                # 🔥 HASH untuk deduplicate
                img_hash = hashlib.md5(image_bytes).hexdigest()

                if img_hash in hash_map:
                    filename = hash_map[img_hash]
                else:
                    img = Image.open(BytesIO(image_bytes))

                    # 🔥 resize
                    img.thumbnail((800, 800))

                    # 🔥 convert + compress
                    buffer = BytesIO()
                    img.convert("RGB").save(
                        buffer,
                        format="JPEG",
                        quality=55,
                        optimize=True
                    )

                    compressed = buffer.getvalue()

                    filename = f"img_{len(image_data)+1}.jpg"

                    image_data[filename] = base64.b64encode(compressed).decode()
                    hash_map[img_hash] = filename

                image_map[index] = filename
                index += 1

            except Exception:
                continue

    return image_map, image_data


def replace_image_placeholder(text, image_map, image_data, used_images):
    """
    Replace placeholder + track used images
    """

    for idx, filename in image_map.items():

        placeholder = f"----media/image{idx}.png----"

        if placeholder in text:
            text = text.replace(
                placeholder,
                f'<img src="@@PLUGINFILE@@/{filename}" />'
            )

            used_images[filename] = image_data[filename]

    return text


def append_images_to_xml(xml, used_images):
    """
    append ONLY used images
    """

    for name, data in used_images.items():
        xml.append(
            f'<file name="{name}" encoding="base64">{data}</file>'
        )
