from core.hybrid_reader import read_docx_hybrid
from core.parser_engine import parse


def run_parser(path):
    elements = read_docx_hybrid(path)
    return parse(elements), elements
