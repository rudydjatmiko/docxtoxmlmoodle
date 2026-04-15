import string

class Question:
    def __init__(self):
        self.content = []
        self.choices = []
        self.answers = []

    def add_content(self, el):
        self.content.append(el)

    def finalize(self):
        lines = [c["text"].strip() for c in self.content if c["text"].strip()]

        if not lines:
            self.choices = []
            return

        split_index = len(lines)

        for i, line in enumerate(lines):
            if len(line) < 50:
                split_index = i
                break

        self.question_text = lines[:split_index]
        choice_lines = lines[split_index:]

        if not choice_lines:
            self.choices = []
            return

        labels = list(string.ascii_uppercase)

        self.choices = []
        for i, c in enumerate(choice_lines):
            label = labels[i] if i < len(labels) else f"X{i}"

            self.choices.append({
                "label": label,
                "text": c
            })
