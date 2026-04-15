def extract_answer(text):
    raw = text.replace("ANS:", "").strip()
    raw = raw.replace("and", ",")
    return [x.strip() for x in raw.split(",")]


def is_type(text):
    t = text.upper()
    if "MULTIPLE CHOICE" in t:
        return "MC"
    if "ESSAY" in t:
        return "ESSAY"
    return None


def parse(elements):

    questions = []

    header = []
    current = None
    current_type = None

    for el in elements:

        text = el["text"].strip()
        level = el.get("level")

        if not text and not el.get("has_drawing"):
            continue

        # ======================
        # 1. HEADER
        # ======================
        if current_type is None:
            t = is_type(text)
            if t:
                current_type = t
            else:
                header.append(text)
            continue

        # ======================
        # 2. GANTI TIPE SOAL
        # ======================
        t = is_type(text)
        if t:
            current_type = t
            continue

        # ======================
        # 3. SOAL BARU (LEVEL 0)
        # ======================
        if level == 0:

            # simpan soal sebelumnya jika belum tersimpan
            if current and current["answers"]:
                questions.append(current)

            current = {
                "type": current_type,
                "question": [],
                "choices": [],
                "answers": []
            }

            current["question"].append(text)
            continue

        # ======================
        # 4. ANS (AKHIR SOAL)
        # ======================
        if text.upper().startswith("ANS"):

            if current:
                current["answers"] = extract_answer(text)
                questions.append(current)
                current = None

            continue

        # ======================
        # 5. PILIHAN (KHUSUS MC)
        # ======================
        if current_type == "MC" and level == 1:
            if current:
                current["choices"].append(text)
            continue

        # ======================
        # 6. ISI SOAL
        # ======================
        if current:
            current["question"].append(text)

    return questions
