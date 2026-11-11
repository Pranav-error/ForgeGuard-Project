"""Fusion & Scoring -- FR-D5, FR-D6, O5, O6 (Detailed Design Document Section 5).
Extended in Phase 2 with a fourth, optional evidence source: the anomaly detector
(Gap 8 / O8). The interface stays additive -- callers that only ever pass
signature/tamper/ocr (anomaly=None) see unchanged behaviour.

Each input sub-score is normalised to a common "evidence toward genuine"
direction (0 = fully forged, 100 = fully genuine) before weighting:
  - signature similarity is already genuine-direction.
  - the tamper module's score is forgery-confidence (higher = more tampered),
    so it is inverted here: tamper_sub_score = 100 - tamper["score"].
  - the OCR sub-score is already genuine-direction (fraction of fields/
    arithmetic that passed).
  - the anomaly detector's score is anomaly-confidence (higher = less like a
    genuine page), so it is inverted the same way as tamper.
A missing sub-score never lets the result reach "Genuine" (5.6 in the
Detailed Design Document): its weight is redistributed across whatever
evidence is available, and the label is capped at "Suspicious".
"""
DEFAULT_WEIGHTS = {"signature": 0.3, "tamper": 0.3, "ocr": 0.2, "anomaly": 0.2}
GENUINE_THRESHOLD = 80
SUSPICIOUS_FLOOR = 40


def _normalise(signature: dict | None, tamper: dict | None, ocr: dict | None, anomaly: dict | None) -> dict:
    subs = {"signature": None, "tamper": None, "ocr": None, "anomaly": None}
    if signature and signature.get("similarity") is not None:
        # similarity is cosine similarity between L2-normalised embeddings (encoder.py),
        # so it ranges over [-1, 1], not [0, 1] -- round(100 * similarity) let a strongly
        # dissimilar (impostor) signature produce a negative sub-score, breaking the 0-100
        # contract every caller (UI, PDF report, README) assumes. Found live by testing the
        # impostor_signature.png demo document, not by the synthetic self-check fixtures.
        subs["signature"] = round(100 * max(-1.0, min(1.0, signature["similarity"])) / 2 + 50)
    if tamper and tamper.get("score") is not None:
        subs["tamper"] = 100 - tamper["score"]
    if ocr and ocr.get("ocr_sub_score") is not None:
        subs["ocr"] = ocr["ocr_sub_score"]
    if anomaly and anomaly.get("score") is not None:
        subs["anomaly"] = 100 - anomaly["score"]
    return subs


def _reason(available: dict, missing: set) -> str:
    parts = []
    if available:
        lowest_key = min(available, key=available.get)
        parts.append(f"lowest-confidence check: {lowest_key} ({available[lowest_key]}/100)")
    if missing:
        parts.append(f"missing evidence: {', '.join(sorted(missing))}")
    return "; ".join(parts) if parts else "all checks passed with high confidence"


def score(
    signature: dict | None,
    tamper: dict | None,
    ocr: dict | None,
    anomaly: dict | None = None,
    weights: dict | None = None,
) -> dict:
    weights = weights or DEFAULT_WEIGHTS
    subs = _normalise(signature, tamper, ocr, anomaly)
    available = {k: v for k, v in subs.items() if v is not None}
    missing = set(subs) - set(available)

    if not available:
        return {"score": None, "label": "Failed", "reason": "all evidence unavailable", "sub_scores": subs}

    total_weight = sum(weights[k] for k in available)
    final_score = round(sum(weights[k] * v for k, v in available.items()) / total_weight)

    if missing:
        label = "Suspicious" if final_score >= SUSPICIOUS_FLOOR else "Forged"
    elif final_score >= GENUINE_THRESHOLD:
        label = "Genuine"
    elif final_score >= SUSPICIOUS_FLOOR:
        label = "Suspicious"
    else:
        label = "Forged"

    return {"score": final_score, "label": label, "reason": _reason(available, missing), "sub_scores": subs}
