"""Per-document-type field extraction and format validation -- FR-D3."""
import re

DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
ID_RE = re.compile(r"\b[A-Z][A-Z0-9]{5,11}\b")
AMOUNT_RE = re.compile(r"(?:total|net|tax)\s*[:\-]?\s*\$?\s*([\d,]+\.\d{2})", re.IGNORECASE)

FINANCIAL_TYPES = {"invoice", "receipt", "bank_statement"}

RULES = {
    "identity": {"date": DATE_RE, "id_number": ID_RE},
    "certificate": {"date": DATE_RE, "id_number": ID_RE},
    "legal": {"date": DATE_RE},
    "invoice": {"date": DATE_RE, "total": None, "net": None, "tax": None},  # amounts via extract_amounts
    "receipt": {"date": DATE_RE, "total": None, "net": None, "tax": None},
    "bank_statement": {"date": DATE_RE, "total": None, "net": None, "tax": None},
}


def extract_amounts(text: str) -> dict:
    out = {}
    for label in ("total", "net", "tax"):
        m = re.search(rf"{label}\s*[:\-]?\s*\$?\s*([\d,]+\.\d{{2}})", text, re.IGNORECASE)
        if m:
            out[label] = m.group(1).replace(",", "")
    return out


def extract_fields(text: str, doc_type: str) -> dict:
    rules = RULES.get(doc_type)
    if rules is None:
        return {}

    fields = {}
    if doc_type in FINANCIAL_TYPES:
        fields.update(extract_amounts(text))
        if "date" in rules:
            m = rules["date"].search(text)
            if m:
                fields["date"] = m.group(0)
    else:
        for name, pattern in rules.items():
            m = pattern.search(text)
            if m:
                fields[name] = m.group(0)
    return fields


def validate_fields(fields: dict, doc_type: str) -> dict:
    rules = RULES.get(doc_type)
    if rules is None:
        return {}
    return {name: (name in fields and bool(fields[name])) for name in rules}
