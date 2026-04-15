import string
import re

class Question:
    def __init__(self):
        self.content = []
        self.choices = []
        self.answers = []

    def add_content(self, el):
        self.content.append(el)

    def add_choice(self, el):
        text = el["text"].strip()

        # hapus prefix A. jika ada
        text = re.sub(r"^[A-D]\.\s*", "", text)

        self.choices.append({
            "text": text,
            "images": el.get("images", [])
        })

    def finalize(self):
        if self.choices:
            self.question_text = self.content
            return

        # fallback jika tidak ada numbering
        lines = [c["text"].strip() for c in self.content if c["text"].strip()]

        choice_lines = []

        for line in reversed(lines):
            if len(line.split()) <= 10:
                choice_lines.insert(0, line)
            else:
                break

        question_lines = lines[:-len(choice_lines)]

        labels = list(string.ascii_uppercase)

        self.choices = []
        for i, c in enumerate(choice_lines):
            self.choices.append({
                "label": labels[i],
                "text": c
            })

        self.question_text = question_lines
