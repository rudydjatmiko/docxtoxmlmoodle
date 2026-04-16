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

        text = el["text"]
        level = el["level"]

        if not text:
            continue

        # TYPE
        t = is_type(text)
        if t:
            current_type = t
            current = None
            continue

        # ======================
        # ESSAY
        # ======================
        if current_type == "ESSAY":

            if current is None:
                q_counter += 1
                current = {
                    "number": f"{q_counter:02d}",
                    "type": "ESSAY",
                    "question": [],
                    "choices": [],
                    "answers": []
                }

            if text.upper().startswith("ANS"):
                questions.append(current)
                current = None
                continue

            current["question"].append(text)
            continue

        # ======================
        # MC
        # ======================
        if current_type == "MC":

            if current is None:
                q_counter += 1
                choice_counter = 0

                current = {
                    "number": f"{q_counter:02d}",
                    "type": "MC",
                    "question": [],
                    "choices": [],
                    "answers": []
                }

            if text.upper().startswith("ANS"):
                current["answers"] = extract_answer(text)
                questions.append(current)
                current = None
                continue

            # pilihan
            if level == 1 or len(text.split()) <= 6:
                label = string.ascii_uppercase[len(current["choices"])]
                current["choices"].append({
                    "label": label,
                    "text": text
                })
                continue

            current["question"].append(text)

    return questions
