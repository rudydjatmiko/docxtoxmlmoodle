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


def is_short(text):
    return len(text.split()) <= 10


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
        # DETEKSI TIPE
        # ======================
        t = is_type(text)
        if t:
            current_type = t
            current = None
            continue

        # ======================
        # ===== ESSAY =====
        # ======================
        if current_type == "ESSAY":

            # START (hanya sekali)
            if current is None and (level == 0 or level is None):
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

            # END
            if text.upper().startswith("ANS"):
                if current:
                    current["answers"] = []
                    questions.append(current)
                    current = None
                continue

            # isi
            if current:
                current["question"].append(text)

            continue

        # ======================
        # ===== MC =====
        # ======================
        if current_type == "MC":

            # START (fleksibel)
            if current is None and (level == 0 or level is None):

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

            # END
            if text.upper().startswith("ANS"):
                if current:
                    current["answers"] = extract_answer(text)

                    # fallback: kalau pilihan kosong
                    if not current["choices"]:
                        temp = []

                        for line in reversed(current["question"]):
                            if is_short(line):
                                temp.insert(0, line)
                            else:
                                break

                        q_len = len(current["question"]) - len(temp)
                        current["choices"] = [
                            {"label": string.ascii_uppercase[i], "text": c}
                            for i, c in enumerate(temp)
                        ]
                        current["question"] = current["question"][:q_len]

                    questions.append(current)
                    current = None
                continue

            # PILIHAN (level benar)
            if level == 1 and current:

                label = string.ascii_uppercase[choice_counter]

                current["choices"].append({
                    "label": label,
                    "text": text
                })

                choice_counter += 1
                continue

            # fallback pilihan (tanpa level)
            if current and not current["choices"] and is_short(text):
                # kemungkinan pilihan
                pass

            # isi soal
            if current:
                current["question"].append(text)

    return questions
