"""Module-facing interface -- Phase 2, Gap 8 / O8, NFR-7.

AnomalyDetectionService.predict() follows the same fixed-interface pattern
as every other detector (TamperLocalisationService.predict(),
SignatureService.verify(), OCRService.check()): image in, a small dict out.
It slots into fusion as a fourth, optional sub-score without changing the
orchestrator, FR-D5, or any other detector (NFR-7) -- which is exactly what
Gap 8 asked for: a way to add coverage for unseen forgery types later
without redesigning the pipeline. "Later" is now.
"""
import numpy as np
import torch
from PIL import Image

from .dataset import SIZE
from .model import ConvAutoencoder

DEFAULT_THRESHOLD = 0.00071  # mean + 2*std of genuine reconstruction error from a 15-epoch
                              # training run (see anomaly_detection.evaluate); recalibrate
                              # with the same command after retraining on new data
SCALE = 6  # score saturates at SCALE*threshold error
# ponytail: the autoencoder's genuine-error variance is tight (std 7e-5), so a
# score scaled against a narrow multiple of `threshold` saturates almost any
# out-of-sample genuine page to 100, not just real forgeries -- observed live
# (0.0019, ~2.7x threshold, saturated under a 2x scale). SCALE=6 gives real
# forgeries (observed ~0.013, ~18x threshold) room to sit clearly above
# marginal genuine pages instead of both reading as "100". Re-tune SCALE
# against a held-out, non-training-distribution genuine sample before
# trusting this on real documents -- the threshold itself only ever saw
# training-distribution data.


class AnomalyDetectionService:
    def __init__(self, checkpoint: str | None = None, device: str | None = None, threshold: float = DEFAULT_THRESHOLD):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.threshold = threshold
        self.model = ConvAutoencoder().to(self.device)
        if checkpoint:
            self.model.load_state_dict(torch.load(checkpoint, map_location=self.device))
        self.model.eval()

    @torch.no_grad()
    def predict(self, image: Image.Image) -> dict:
        arr = np.asarray(image.convert("RGB").resize((SIZE, SIZE)), dtype=np.float32) / 255.0
        x = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(self.device)
        recon = self.model(x)
        error = float(((recon - x) ** 2).mean().cpu())
        score = int(round(100 * min(error / (SCALE * self.threshold), 1.0))) if self.threshold > 0 else 0
        return {"score": score, "reconstruction_error": error}
