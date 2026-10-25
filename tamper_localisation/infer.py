"""Module-facing interface -- FR-D1, FR-D2, FR-D6, NFR-7.

TamperLocalisationService.predict() is the fixed contract the System Design
Document's orchestrator calls: a document image in, a mask/heatmap/score/
regions dict out. Swapping the model inside this class should never require
changing the orchestrator or the other detector services.
"""
import numpy as np
import torch
from PIL import Image
from scipy import ndimage

from .model import TamperLocaliser
from .preprocess import preprocess

MAX_REGIONS = 5


class TamperLocalisationService:
    def __init__(self, checkpoint: str | None = None, device: str | None = None, img_size: int = 256):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.img_size = img_size
        self.model = TamperLocaliser(img_size=img_size).to(self.device)
        if checkpoint:
            self.model.load_state_dict(torch.load(checkpoint, map_location=self.device))
        self.model.eval()

    @torch.no_grad()
    def predict(self, image: Image.Image, threshold: float = 0.5) -> dict:
        pre = preprocess(image, size=self.img_size)
        rgb = torch.from_numpy(pre["rgb"]).float().unsqueeze(0).to(self.device)
        ela = torch.from_numpy(pre["ela"]).float().unsqueeze(0).unsqueeze(0).to(self.device)

        heatmap = torch.sigmoid(self.model(rgb, ela))[0, 0].cpu().numpy()  # (H, W) in [0, 1]
        mask = (heatmap >= threshold).astype(np.uint8) * 255

        regions = self._top_regions(heatmap, threshold)
        score = self._tamper_score(heatmap, mask)
        return {"mask": mask, "heatmap": heatmap, "score": score, "regions": regions}

    @staticmethod
    def _top_regions(heatmap: np.ndarray, threshold: float, max_regions: int = MAX_REGIONS) -> list[dict]:
        binary = heatmap >= threshold
        labeled, n = ndimage.label(binary)
        if n == 0:
            return []
        sizes = ndimage.sum(binary, labeled, range(1, n + 1))
        order = np.argsort(sizes)[::-1][:max_regions]
        slices = ndimage.find_objects(labeled)
        regions = []
        for i in order:
            label_id = i + 1
            sl = slices[label_id - 1]
            y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
            regions.append(
                {
                    "bbox": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
                    "confidence": float(heatmap[sl][labeled[sl] == label_id].mean()),
                }
            )
        return regions

    @staticmethod
    def _tamper_score(heatmap: np.ndarray, mask: np.ndarray) -> int:
        """0-100: weighted blend of peak confidence and flagged-area coverage."""
        peak = float(heatmap.max())
        coverage = float((mask > 0).mean())
        coverage_term = min(coverage / 0.2, 1.0)  # saturate once >=20% of the page is flagged
        return int(round(100 * (0.6 * peak + 0.4 * coverage_term)))
