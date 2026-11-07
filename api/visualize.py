"""Heatmap overlay for FR-D6 ("heatmap... presented to a verifier")."""
import numpy as np
from PIL import Image


def overlay_heatmap(page: Image.Image, heatmap_hw: np.ndarray, alpha: float = 0.5) -> Image.Image:
    """page: original upload. heatmap_hw: (H,W) in [0,1], as returned by TamperLocalisationService."""
    size = heatmap_hw.shape[0]
    base = np.asarray(page.convert("RGB").resize((size, size)), dtype=np.float32) / 255.0
    red = np.zeros_like(base)
    red[..., 0] = 1.0
    blended = base * (1 - alpha * heatmap_hw[..., None]) + red * (alpha * heatmap_hw[..., None])
    out = np.clip(blended * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode="RGB")
