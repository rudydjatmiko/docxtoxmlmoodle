import string

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

    current = None
    current_type = None

    q_counter = 0
    choice_counter = 0  # 🔥 untuk A, B, C

    for el in elements:

        text = el["text"].strip()
        level = el.get("level")

        if not text and not el.get("has_drawing"):
            continue

        # ======================
        # DETEKSI TIPE
        # ======================
        t = is_type(text)
        if t:
            current_type = t
            continue

        # ======================
        # START SOAL
        # ======================
        if level == 0 and current is None:

            q_counter += 1
            choice_counter = 0  # 🔥 reset pilihan

            current = {
                "number": f"{q_counter:02d}",
                "type": current_type,
                "question": [],
                "choices": [],
                "answers": []
            }

            current["question"].append(text)
            continue

        # ======================
        # END SOAL
        # ======================
        if text.upper().startswith("ANS"):

            if current:
                current["answers"] = extract_answer(text)
                questions.append(current)
                current = None

            continue

        # ======================
        # PILIHAN (MC)
        # ======================
        if current_type == "MC" and level == 1:

            if current:
                label = string.ascii_uppercase[choice_counter]

                current["choices"].append({
                    "label": label,
                    "text": text
                })

                choice_counter += 1

            continue

        # ======================
        # ISI SOAL
        # ======================
        if current:
            current["question"].append(text)

    return questions
