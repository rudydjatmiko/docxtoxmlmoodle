from core.parser_engine import parse
from processors.content_processor import process

def run_parser(elements):
    elements = process(elements)
    return parse(elements)
