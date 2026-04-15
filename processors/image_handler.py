import base64
import uuid

def extract_images(el):
    images = []

    for img_xml in el.get("images", []):
        # dummy handler (real extraction bisa di-upgrade)
        name = f"{uuid.uuid4().hex}.png"
        data = base64.b64encode(img_xml.encode()).decode()

        images.append({
            "name": name,
            "data": data
        })

    return images
