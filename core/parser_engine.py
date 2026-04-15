from core.detector import (
    is_question, is_option, is_answer_key,
    extract_question, extract_option, extract_answer
)
from models.question import Question


def parse_lines(lines, logs):
    questions = []

    current = None

    for line in lines:

        # ===== START QUESTION =====
        if is_question(line):
            if current:
                questions.append(current)

            current = Question()
            current.text = extract_question(line)
            continue

        # ===== OPTION =====
        if is_option(line) and current:
            current.options.append(extract_option(line))
            continue

        # ===== ANSWER KEY =====
        if is_answer_key(line) and current:
            current.correct = extract_answer(line)
            questions.append(current)
            current = None
            continue

        # ===== MULTILINE =====
        if current:
            if current.options:
                current.options[-1] += "<br/>" + line
            else:
                current.text += "<br/>" + line

    return questions
