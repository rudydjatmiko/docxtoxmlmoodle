import re

RE_QUESTION = re.compile(r'^\d+[\.\)]\s+')
RE_OPTION = re.compile(r'^\(?([A-Da-d])[\.\)]\s+')
RE_ANS = re.compile(r'^ANS\s*[:\-]?\s*(.*)', re.IGNORECASE)


def is_question(line):
    return bool(RE_QUESTION.match(line))


def is_option(line):
    return bool(RE_OPTION.match(line))


def is_answer_key(line):
    return bool(RE_ANS.match(line))


def extract_question(line):
    return RE_QUESTION.sub('', line).strip()


def extract_option(line):
    return RE_OPTION.sub('', line).strip()


def extract_answer(line):
    match = RE_ANS.match(line)
    if not match:
        return []
    return re.findall(r'[A-D]', match.group(1).upper())
