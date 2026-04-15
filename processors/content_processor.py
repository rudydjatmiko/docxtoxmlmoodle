from processors.image_handler import extract_images

def process(elements):
    processed = []

    for el in elements:
        item = {
            "text": el.get("text", ""),
            "images": extract_images(el)
        }
        processed.append(item)

    return processed
