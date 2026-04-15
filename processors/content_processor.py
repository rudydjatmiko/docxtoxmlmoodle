def process(elements):
    # SEKARANG tidak perlu extract_images lagi di sini
    # karena image sudah di-handle di docx_reader

    processed = []

    for el in elements:
        processed.append({
            "text": el.get("text", ""),
            "images": el.get("images", [])
        })

    return processed
