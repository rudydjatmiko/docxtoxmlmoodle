from models.question import Question

def is_ans(text):
    return text.strip().startswith("ANS:")

def extract_answer(text):
    raw = text.replace("ANS:", "").strip()
    return [x.strip() for x in raw.split(",")]

def parse(elements):
    questions = []
    current = Question()

    for el in elements:
        text = el["text"].strip()

        if not text:
            continue

        if is_ans(text):
            current.answers = extract_answer(text)
            current.finalize()
            questions.append(current)
            current = Question()
            continue

        current.add_content(el)

    return questions
