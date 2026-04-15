import re

def clean_lines(text):
    return [l.strip() for l in text.split('\n') if l.strip()]


def wrap_arabic(text):
    pattern = re.compile(r'([\u0600-\u06FF]+)')
    return pattern.sub(
        r'<span dir="rtl" style="font-size:22px;">\1</span>',
        text
    )
