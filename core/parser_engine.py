import re

def extract_answer(text):
    raw = text.replace("ANS:", "").strip()
    raw = raw.replace("and", ",")
    return [x.strip() for x in raw.split(",")]


def is_short(text):
    return len(text.split()) <= 12


def parse(elements):

    questions = []
    current = {
        "question": [],
        "choices": [],
        "answers": []
    }

    buffer = []

    for el in elements:

        text = el["text"].strip()
        level = el.get("level")

        if not text and not el.get("has_drawing"):
            continue

        # ===== ANSWER (END OF QUESTION)
        if text.upper().startswith("ANS"):
            current["answers"] = extract_answer(text)

            # 🔥 SPLIT QUESTION vs CHOICES (fallback)
            if not current["choices"]:

                choices = []

                for line in reversed(current["question"]):
                    if is_short(line):
                        choices.insert(0, line)
                    else:
                        break

                q_len = len(current["question"]) - len(choices)

                current["choices"] = choices
                current["question"] = current["question"][:q_len]

            questions.append(current)

            current = {
                "question": [],
                "choices": [],
                "answers": []
            }

            continue

        # ===== CHOICE BY LEVEL
        if level == 1:
            current["choices"].append(text)
            continue

        # ===== DEFAULT MASUK KE QUESTION
        current["question"].append(text)

    return questions
