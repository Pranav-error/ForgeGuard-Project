"""Module-facing interface -- FR-D3, FR-D4, NFR-7."""
from PIL import Image

from . import arithmetic, fields as field_rules
from .engine import extract_text
from .fields import FINANCIAL_TYPES


class OCRService:
    def check(self, page: Image.Image, doc_type: str) -> dict:
        text = extract_text(page)
        extracted = field_rules.extract_fields(text, doc_type)
        flags = field_rules.validate_fields(extracted, doc_type)

        arithmetic_ok = arithmetic.check(extracted) if doc_type in FINANCIAL_TYPES else None

        if not flags:
            pass_fraction = 1.0  # no rule set for this doc_type: nothing to fail (2.6 in the Detailed Design Doc)
        else:
            pass_fraction = sum(flags.values()) / len(flags)
        arithmetic_penalty = 0.5 if arithmetic_ok is False else 1.0
        score = round(100 * pass_fraction * arithmetic_penalty)

        return {"fields": extracted, "flags": flags, "arithmetic_ok": arithmetic_ok, "ocr_sub_score": score}
