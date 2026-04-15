from core.docx_reader import read_docx
from parser import run_parser
from core.builder import build_xml

INPUT = "input.docx"
OUTPUT = "output.xml"

def main():
    print("📥 Reading DOCX...")
    elements = read_docx(INPUT)

    print("⚙️ Parsing...")
    questions = run_parser(elements)

    print("🧾 Building XML...")
    xml = build_xml(questions)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(xml)

    print("✅ DONE:", OUTPUT)

if __name__ == "__main__":
    main()
