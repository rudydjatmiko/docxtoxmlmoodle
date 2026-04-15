from models.question import Question

def is_ans(text):
    return text.strip().startswith("ANS:")

def extract_answer(text):
    raw = text.replace("ANS:", "").strip()
    raw = raw.replace("and", ",")
    return [x.strip() for x in raw.split(",")]

def parse(elements):
    questions = []
    current = Question()

    for el in elements:
        text = el["text"].strip()
        num = el.get("numbering")

        if not text and not el.get("has_drawing"):
            continue

        # ======================
        # DETEKSI JAWABAN
        # ======================
        if is_ans(text):
            current.answers = extract_answer(text)
            current.finalize()
            questions.append(current)
            current = Question()
            continue

        # ======================
        # DETEKSI PILIHAN (LEVEL 1)
        # ======================
        if num and num.get("level") == 1:
            current.add_choice(el)
            continue

        # ======================
        # DETEKSI SOAL (LEVEL 0)
        # ======================
        if num and num.get("level") == 0:
            if current.content:
                questions.append(current)
                current = Question()

        current.add_content(el)

    return questions
