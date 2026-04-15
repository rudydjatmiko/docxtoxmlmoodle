import base64
from PIL import Image
import io

def get_image_map(doc):
    rels = doc.part._rels
    image_map = {}

    for rel in rels:
        rel = rels[rel]
        if "image" in rel.target_ref:
            image_map[rel.rId] = rel.target_part

    return image_map


def compress_image(image_bytes, max_width=800, quality=75):
    """
    Resize + compress image
    """
    img = Image.open(io.BytesIO(image_bytes))

    # convert ke RGB kalau perlu (hindari error PNG)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # resize jika terlalu besar
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height))

    # simpan ke buffer
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)

    return buffer.getvalue()


def extract_images_from_paragraph(paragraph, image_map):
    images = []

    blips = paragraph._element.xpath('.//a:blip')

    for blip in blips:
        rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')

        if rId in image_map:
            part = image_map[rId]

            raw_bytes = part.blob

            # 🔥 COMPRESS DI SINI
            image_bytes = compress_image(raw_bytes)

            filename = part.partname.split("/")[-1]
            filename = filename.split(".")[0] + ".jpg"  # convert ke jpg

            encoded = base64.b64encode(image_bytes).decode("utf-8")

            images.append({
                "name": filename,
                "data": encoded
            })

    return images
