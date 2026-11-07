"""Self-check: python3 -m ocr_validation.test_module"""
from PIL import Image, ImageDraw

from . import arithmetic, fields as field_rules
from .engine import extract_text
from .service import OCRService


def test_extract_fields_identity():
    text = "Name: Jane Doe\nDOB: 05/06/1990\nID: AB123456\n"
    extracted = field_rules.extract_fields(text, "identity")
    assert extracted.get("date") == "05/06/1990"
    assert extracted.get("id_number") == "AB123456"
    flags = field_rules.validate_fields(extracted, "identity")
    assert flags == {"date": True, "id_number": True}


def test_extract_amounts_invoice():
    text = "Invoice\nDate: 01/02/2026\nNet: $100.00\nTax: $10.00\nTotal: $110.00\n"
    extracted = field_rules.extract_fields(text, "invoice")
    assert extracted["total"] == "110.00"
    assert extracted["net"] == "100.00"
    assert extracted["tax"] == "10.00"


def test_arithmetic_gate():
    assert arithmetic.check({"total": "110.00", "net": "100.00", "tax": "10.00"}) is True
    assert arithmetic.check({"total": "150.00", "net": "100.00", "tax": "10.00"}) is False
    assert arithmetic.check({"total": "110.00", "net": "100.00"}) is None  # missing field


def test_unknown_doc_type_no_rules():
    extracted = field_rules.extract_fields("whatever text", "unknown_type")
    flags = field_rules.validate_fields(extracted, "unknown_type")
    assert extracted == {} and flags == {}


def test_tesseract_round_trip():
    img = Image.new("RGB", (500, 120), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "Date: 01/02/2026 ID: AB123456", fill=(0, 0, 0))
    text = extract_text(img)
    assert "2026" in text or "AB123456" in text  # OCR of rendered text is not 100% exact


def test_service_end_to_end_identity():
    img = Image.new("RGB", (500, 150), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), "Date: 01/02/2026", fill=(0, 0, 0))
    draw.text((10, 70), "ID: AB123456", fill=(0, 0, 0))
    out = OCRService().check(img, "identity")
    assert "fields" in out and "flags" in out
    assert out["arithmetic_ok"] is None
    assert 0 <= out["ocr_sub_score"] <= 100


def main():
    test_extract_fields_identity()
    test_extract_amounts_invoice()
    test_arithmetic_gate()
    test_unknown_doc_type_no_rules()
    test_tesseract_round_trip()
    test_service_end_to_end_identity()
    print("all demo checks passed")


if __name__ == "__main__":
    main()
