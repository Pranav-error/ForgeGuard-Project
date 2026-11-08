"""Heatmap overlay for FR-D6 ("heatmap... presented to a verifier").

# ponytail: on genuinely out-of-distribution input (a random photo, not a
# document -- the model was never meant to see one), a continuous heatmap
# blend can saturate across the whole frame and render as a solid red wash,
# which reads as "broken" rather than "here is the suspicious region."
# Tinting only the thresholded mask, plus drawing boxes around the actual
# top regions, stays legible (and honest) even when the input is nonsense.
"""
import numpy as np
from PIL import Image, ImageDraw

MASK_ALPHA = 0.38
BOX_COLOR = (220, 38, 38)


def overlay_heatmap(page: Image.Image, heatmap_hw: np.ndarray, regions: list[dict], threshold: float = 0.5) -> Image.Image:
    """page: original upload. heatmap_hw: (H,W) in [0,1]. regions: TamperLocalisationService's
    top-N {bbox, confidence} list, already in heatmap-pixel coordinates."""
    size = heatmap_hw.shape[0]
    base = np.asarray(page.convert("RGB").resize((size, size)), dtype=np.float32) / 255.0

    mask = heatmap_hw >= threshold
    red = np.zeros_like(base)
    red[..., 0] = 1.0
    blended = np.where(mask[..., None], base * (1 - MASK_ALPHA) + red * MASK_ALPHA, base)
    out = Image.fromarray(np.clip(blended * 255, 0, 255).astype(np.uint8), mode="RGB")

    if regions:
        draw = ImageDraw.Draw(out)
        for i, region in enumerate(regions, start=1):
            x, y, w, h = region["bbox"]
            draw.rectangle([x, y, x + w, y + h], outline=BOX_COLOR, width=2)
            draw.text((x + 2, max(y - 12, 0)), str(i), fill=BOX_COLOR)

    return out
