"""Self-check: python3 -m fusion.test_module"""
from .service import score


def test_all_genuine():
    sig = {"similarity": 0.95}
    tamper = {"score": 5}       # low forgery confidence -> high genuine evidence
    ocr = {"ocr_sub_score": 100}
    anomaly = {"score": 5}      # low anomaly confidence -> high genuine evidence
    out = score(sig, tamper, ocr, anomaly)
    assert out["label"] == "Genuine"
    assert out["score"] >= 80


def test_all_forged():
    sig = {"similarity": 0.1}
    tamper = {"score": 90}      # high forgery confidence
    ocr = {"ocr_sub_score": 20}
    anomaly = {"score": 85}     # high anomaly confidence
    out = score(sig, tamper, ocr, anomaly)
    assert out["label"] == "Forged"


def test_missing_evidence_never_genuine():
    sig = {"similarity": 0.99}
    tamper = {"score": 0}
    ocr = None  # OCR unavailable
    anomaly = {"score": 0}
    out = score(sig, tamper, ocr, anomaly)
    assert out["label"] != "Genuine"  # capped even though available evidence is perfect
    assert "ocr" in out["reason"]


def test_anomaly_missing_also_caps_below_genuine():
    sig = {"similarity": 0.99}
    tamper = {"score": 0}
    ocr = {"ocr_sub_score": 100}
    out = score(sig, tamper, ocr, anomaly=None)
    assert out["label"] != "Genuine"
    assert "anomaly" in out["reason"]


def test_all_missing():
    out = score(None, None, None, None)
    assert out["label"] == "Failed"
    assert out["score"] is None


def test_tamper_direction_inverted():
    # identical signature/ocr/anomaly evidence, only tamper confidence differs
    sig, ocr, anomaly = {"similarity": 0.9}, {"ocr_sub_score": 90}, {"score": 10}
    low_tamper = score(sig, {"score": 0}, ocr, anomaly)
    high_tamper = score(sig, {"score": 100}, ocr, anomaly)
    assert low_tamper["score"] > high_tamper["score"]


def test_anomaly_direction_inverted():
    # identical signature/tamper/ocr evidence, only anomaly confidence differs
    sig, tamper, ocr = {"similarity": 0.9}, {"score": 10}, {"ocr_sub_score": 90}
    low_anomaly = score(sig, tamper, ocr, {"score": 0})
    high_anomaly = score(sig, tamper, ocr, {"score": 100})
    assert low_anomaly["score"] > high_anomaly["score"]


def test_backward_compatible_without_anomaly_arg():
    # callers that never pass anomaly still get a sane (capped) result, not an error
    out = score({"similarity": 0.9}, {"score": 10}, {"ocr_sub_score": 90})
    assert out["label"] in ("Suspicious", "Forged")
    assert out["score"] is not None


def main():
    test_all_genuine()
    test_all_forged()
    test_missing_evidence_never_genuine()
    test_anomaly_missing_also_caps_below_genuine()
    test_all_missing()
    test_tamper_direction_inverted()
    test_anomaly_direction_inverted()
    test_backward_compatible_without_anomaly_arg()
    print("all demo checks passed")


if __name__ == "__main__":
    main()
