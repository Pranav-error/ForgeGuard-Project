"""Arithmetic consistency gate for financial documents -- FR-D4."""

TOLERANCE = 0.02  # relative tolerance on total vs net + tax


def check(fields: dict) -> bool | None:
    """None = not applicable (fields missing), True/False = gate result."""
    try:
        total = float(fields["total"])
        net = float(fields["net"])
        tax = float(fields["tax"])
    except (KeyError, ValueError):
        return None
    expected = net + tax
    return abs(total - expected) <= TOLERANCE * max(abs(total), 1.0)
