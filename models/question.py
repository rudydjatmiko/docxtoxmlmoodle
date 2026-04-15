import string

def finalize(self):
    lines = [c["text"].strip() for c in self.content if c["text"].strip()]

    # ======================
    # SAFETY: jika kosong
    # ======================
    if not lines:
        self.question_text = []
        self.choices = []
        return

    # ======================
    # SPLIT soal vs pilihan
    # ======================
    split_index = len(lines)

    for i, line in enumerate(lines):
        if len(line) < 50:
            split_index = i
            break

    self.question_text = lines[:split_index]
    choice_lines = lines[split_index:]

    # ======================
    # SAFETY: jika tidak ada pilihan
    # ======================
    if not choice_lines:
        self.choices = []
        return

    # ======================
    # LABEL DINAMIS
    # ======================
    labels = list(string.ascii_uppercase)

    self.choices = []

    for i, c in enumerate(choice_lines):
        # SAFE LABEL
        if i < len(labels):
            label = labels[i]
        else:
            label = f"X{i}"

        self.choices.append({
            "label": label,
            "text": c
        })
