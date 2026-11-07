"""Self-check: python3 -m fusion.test_module"""
from .service import score


def test_all_genuine():
    sig = {"similarity": 0.95}
    tamper = {"score": 5}       # low forgery confidence -> high genuine evidence
    ocr = {"ocr_sub_score": 100}
    out = score(sig, tamper, ocr)
    assert out["label"] == "Genuine"
    assert out["score"] >= 80


def test_all_forged():
    sig = {"similarity": 0.1}
    tamper = {"score": 90}      # high forgery confidence
    ocr = {"ocr_sub_score": 20}
    out = score(sig, tamper, ocr)
    assert out["label"] == "Forged"


def test_missing_evidence_never_genuine():
    sig = {"similarity": 0.99}
    tamper = {"score": 0}
    ocr = None  # OCR unavailable
    out = score(sig, tamper, ocr)
    assert out["label"] != "Genuine"  # capped even though available evidence is perfect
    assert "ocr" in out["reason"]


def test_all_missing():
    out = score(None, None, None)
    assert out["label"] == "Failed"
    assert out["score"] is None


def test_tamper_direction_inverted():
    # identical signature/ocr evidence, only tamper confidence differs
    sig, ocr = {"similarity": 0.9}, {"ocr_sub_score": 90}
    low_tamper = score(sig, {"score": 0}, ocr)
    high_tamper = score(sig, {"score": 100}, ocr)
    assert low_tamper["score"] > high_tamper["score"]


def main():
    test_all_genuine()
    test_all_forged()
    test_missing_evidence_never_genuine()
    test_all_missing()
    test_tamper_direction_inverted()
    print("all demo checks passed")


if __name__ == "__main__":
    main()
