"""Verification Orchestrator -- FR-P1 (Detailed Design Document Section 6).
Phase 2: also runs the anomaly detector and anchors every verification on
the hash-chain ledger (Gap 8/O8 and Gap 9/O9).

# ponytail: runs the four detectors sequentially and synchronously within
# the request (no asyncio fan-out, no per-detector timeout). Fine for a
# single-process prototype; swap in the async fan-out/fan-in from Section
# 6.2 of the Detailed Design Document when concurrent load matters.
"""
import hashlib
import logging

from PIL import Image

from anomaly_detection import AnomalyDetectionService
from fusion import score as fuse_score
from ocr_validation import OCRService
from signature_verification import SignatureService
from tamper_localisation import TamperLocalisationService

from . import db

logger = logging.getLogger("forgeguard.orchestrator")


class Orchestrator:
    def __init__(
        self,
        tamper_checkpoint: str | None = None,
        signature_checkpoint: str | None = None,
        anomaly_checkpoint: str | None = None,
    ):
        self.tamper = TamperLocalisationService(checkpoint=tamper_checkpoint)
        self.signature = SignatureService(checkpoint=signature_checkpoint)
        self.ocr = OCRService()
        self.anomaly = AnomalyDetectionService(checkpoint=anomaly_checkpoint)

    def _run_tamper(self, image: Image.Image) -> dict | None:
        try:
            return self.tamper.predict(image)
        except Exception:
            logger.exception("tamper localisation failed; degrading to missing evidence")
            return None

    def _run_signature(self, image: Image.Image, conn, signer_id: str | None) -> dict | None:
        if not signer_id:
            return None
        try:
            refs = db.get_references(conn, signer_id)
            return self.signature.verify(image, refs)
        except Exception:
            logger.exception("signature verification failed; degrading to missing evidence")
            return None

    def _run_ocr(self, image: Image.Image, doc_type: str) -> dict | None:
        try:
            return self.ocr.check(image, doc_type)
        except Exception:
            logger.exception("OCR/field validation failed; degrading to missing evidence")
            return None

    def _run_anomaly(self, image: Image.Image) -> dict | None:
        try:
            return self.anomaly.predict(image)
        except Exception:
            logger.exception("anomaly detection failed; degrading to missing evidence")
            return None

    def verify(self, conn, image: Image.Image, doc_type: str, signer_id: str | None) -> dict:
        doc_hash = hashlib.sha256(image.tobytes()).hexdigest()  # FR-P2
        document_id = db.add_document(conn, doc_type, doc_hash)

        tamper_out = self._run_tamper(image)
        signature_out = self._run_signature(image, conn, signer_id)
        ocr_out = self._run_ocr(image, doc_type)
        anomaly_out = self._run_anomaly(image)

        fused = fuse_score(signature_out, tamper_out, ocr_out, anomaly_out)

        verification_id = db.add_verification(conn, document_id, fused)
        db.add_audit(conn, "verify", verification_id, {"doc_type": doc_type, "signer_id": signer_id})
        if fused["label"] == "Suspicious":
            db.add_audit(conn, "flagged_for_review", verification_id, {})

        block = db.add_block(conn, document_id, verification_id, doc_hash)  # Phase 2 anchoring
        db.add_audit(conn, "anchored", verification_id, {"block_index": block["index"]})  # block dict key is "index" (ledger.chain.Block.index)

        return {
            "document_id": document_id,
            "verification_id": verification_id,
            "score": fused["score"],
            "label": fused["label"],
            "reason": fused["reason"],
            "sub_scores": fused["sub_scores"],
            "tamper_regions": tamper_out["regions"] if tamper_out else None,
            "signature_bbox": signature_out["bbox"] if signature_out else None,
            "ocr_fields": ocr_out["fields"] if ocr_out else None,
            "anomaly_reconstruction_error": anomaly_out["reconstruction_error"] if anomaly_out else None,
            "ledger_block": {"block_index": block["index"], "block_hash": block["block_hash"]},
            "_heatmap": tamper_out["heatmap"] if tamper_out else None,  # consumed by the API layer, not returned to clients
        }
