import string


def extract_answer(text):
    raw = text.replace("ANS:", "").strip()
    raw = raw.replace("and", ",")
    return [x.strip() for x in raw.split(",") if x.strip()]


def is_type(text):
    t = text.strip().upper()
    if t == "MULTIPLE CHOICE":
        return "MC"
    if t == "ESSAY":
        return "ESSAY"
    return None


def parse(elements):

    questions = []

    current = None
    current_type = None

    q_counter = 0
    choice_counter = 0

    for el in elements:

        text = el.get("text", "").strip()
        level = el.get("level")
        has_drawing = el.get("has_drawing", False)

        if not text and not has_drawing:
            continue

        # ======================
        # DETEKSI TIPE SOAL
        # ======================
        t = is_type(text)
        if t:
            current_type = t
            current = None  # reset soal aktif
            continue

        # ======================
        # ===== ESSAY MODE =====
        # ======================
        if current_type == "ESSAY":

            # START (level 0 pertama)
            if current is None:
                if level == 0:
                    q_counter += 1

                    current = {
                        "number": f"{q_counter:02d}",
                        "type": "ESSAY",
                        "question": [],
                        "choices": [],
                        "answers": []
                    }

                    current["question"].append(text)

                continue

            # END (ANS)
            if text.upper().startswith("ANS"):
                current["answers"] = extract_answer(text)
                questions.append(current)
                current = None
                continue

            # SEMUA MASUK KE SOAL
            current["question"].append(text)
            continue

        # ======================
        # ===== MC MODE =====
        # ======================
        if current_type == "MC":

            # START SOAL
            if level == 0 and current is None:

                q_counter += 1
                choice_counter = 0

                current = {
                    "number": f"{q_counter:02d}",
                    "type": "MC",
                    "question": [],
                    "choices": [],
                    "answers": []
                }

                current["question"].append(text)
                continue

            # END SOAL
            if text.upper().startswith("ANS"):
                if current:
                    current["answers"] = extract_answer(text)
                    questions.append(current)
                    current = None
                continue

            # PILIHAN (level 1)
            if level == 1 and current:

                label = string.ascii_uppercase[choice_counter]

                current["choices"].append({
                    "label": label,
                    "text": text
                })

                choice_counter += 1
                continue

            # ISI SOAL
            if current:
                current["question"].append(text)

    return questions
