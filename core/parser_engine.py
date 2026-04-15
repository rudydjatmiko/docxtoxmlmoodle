import re

def extract_answer(text):
    raw = text.replace("ANS:", "").strip()
    raw = raw.replace("and", ",")
    return [x.strip() for x in raw.split(",")]

def parse(elements):

    questions = []
    current = {
        "question": [],
        "choices": [],
        "answers": []
    }

    for el in elements:

        text = el["text"].strip()
        level = el["level"]

        if not text and not el["has_drawing"]:
            continue

        # ===== ANSWER =====
        if text.upper().startswith("ANS"):
            current["answers"] = extract_answer(text)
            questions.append(current)

            current = {
                "question": [],
                "choices": [],
                "answers": []
            }
            continue

        # ===== CHOICE =====
        if level == 1:
            current["choices"].append(text)
            continue

        # ===== QUESTION =====
        current["question"].append(text)

    return questions
