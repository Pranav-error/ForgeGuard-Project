"""Module-facing interface -- FR-S1, FR-S2, FR-S3, NFR-6, NFR-7.

SignatureService is storage-agnostic: it takes reference embeddings in, not a
signer_id -- looking signer_id up in `signatures` is the orchestrator's job
(Section 3 of the Detailed Design Document), keeping this module swappable
without touching the data layer.
"""
import numpy as np
import torch
from PIL import Image

from .cleaner import clean
from .detector import detect
from .encoder import SignatureEncoder

DEFAULT_THRESHOLD = 0.75


class SignatureService:
    def __init__(self, checkpoint: str | None = None, device: str | None = None, threshold: float = DEFAULT_THRESHOLD):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.threshold = threshold
        self.model = SignatureEncoder().to(self.device)
        if checkpoint:
            self.model.load_state_dict(torch.load(checkpoint, map_location=self.device))
        self.model.eval()

    @torch.no_grad()
    def embed(self, crop: Image.Image) -> np.ndarray:
        """Crop -> clean -> embedding (used both at verify time and to register a reference)."""
        cleaned = clean(crop)
        arr = np.asarray(cleaned.resize((128, 128)), dtype=np.float32) / 255.0
        x = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).to(self.device)
        return self.model(x)[0].cpu().numpy()

    def verify(self, page: Image.Image, references: list[np.ndarray]) -> dict:
        """FR-S3: detect + clean + embed the page's signature, compare to references."""
        if not references:
            return {"similarity": None, "decision": "no_references", "bbox": None}

        found = detect(page)
        if found is None:
            return {"similarity": None, "decision": "not_found", "bbox": None}

        bbox = found["bbox"]
        x, y, w, h = bbox
        crop = page.crop((x, y, x + w, y + h))
        embedding = self.embed(crop)

        sims = [float(np.dot(embedding, ref)) for ref in references]
        similarity = max(sims)
        decision = "genuine" if similarity >= self.threshold else "forged"
        return {"similarity": similarity, "decision": decision, "bbox": bbox}
