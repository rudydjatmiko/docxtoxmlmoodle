def process(elements):
    processed = []

    for el in elements:
        processed.append({
            "text": el.get("text", ""),
            "images": el.get("images", [])
        })

    return processed
