import base64

def get_image_map(doc):
    rels = doc.part._rels
    image_map = {}

    for rel in rels:
        rel = rels[rel]
        if "image" in rel.target_ref:
            image_map[rel.rId] = rel.target_part

    return image_map


def extract_images_from_paragraph(paragraph, image_map):
    images = []

    blips = paragraph._element.xpath('.//a:blip')

    for blip in blips:
        rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')

        if rId in image_map:
            part = image_map[rId]

            image_bytes = part.blob
            filename = part.partname.split("/")[-1]

            encoded = base64.b64encode(image_bytes).decode("utf-8")

            images.append({
                "name": filename,
                "data": encoded
            })

    return images
