class Question:
    def __init__(self):
        self.content = []   # semua isi soal
        self.choices = []
        self.answers = []

    def add_content(self, el):
        self.content.append(el)

    def finalize(self):
        """
        pisahkan content → soal + pilihan
        """
        lines = [c["text"].strip() for c in self.content if c["text"].strip()]

        # heuristik: baris pendek = pilihan
        split_index = 0
        for i, line in enumerate(lines):
            if len(line) < 50:
                split_index = i
                break

        self.question_text = lines[:split_index]
        self.choice_texts = lines[split_index:]

        # generate label
        labels = ["A", "B", "C", "D", "E"]

        self.choices = []
        for i, c in enumerate(self.choice_texts):
            self.choices.append({
                "label": labels[i],
                "text": c
            })
