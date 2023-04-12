"""Test"""
import json

from src.pdf_card import PdfCard
from configparser import ConfigParser


config = ConfigParser()
config.read("./config.ini")
barcode_height, barcode_width = map(int, config.get("GENERAL", "BARCODE_SIZE").split(','))
tagged_barcode_height, tagged_barcode_width = map(int, config.get("GENERAL", "TAGGED_BARCODE_SIZE").split(','))


def test_pdf():
    with open("./test_files/fields.json", "r", encoding="utf-8") as f:
        test_fields = json.load(f)
    card = PdfCard("./test_files/test_task.pdf", test_fields["fields"], test_fields["order"])
    card.validate()
