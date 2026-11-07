"""Signature crop cleaning -- FR-S2: remove ruled lines, stamps, background noise."""
import numpy as np
from PIL import Image
from scipy import ndimage

MIN_BLOB_AREA = 15  # drop specks smaller than this after line removal


def clean(crop: Image.Image) -> Image.Image:
    gray = np.asarray(crop.convert("L"), dtype=np.float32)
    thresh = gray.mean() - 0.5 * gray.std()
    ink = gray < thresh

    # remove long straight (ruled) lines: open with a wide horizontal / vertical structure
    h_line = np.ones((1, max(ink.shape[1] // 3, 3)), dtype=bool)
    v_line = np.ones((max(ink.shape[0] // 3, 3), 1), dtype=bool)
    lines = ndimage.binary_opening(ink, structure=h_line) | ndimage.binary_opening(ink, structure=v_line)
    cleaned = ink & ~lines

    # drop small disconnected specks (noise / stamp fragments)
    labeled, n = ndimage.label(cleaned)
    if n > 0:
        sizes = ndimage.sum(cleaned, labeled, range(1, n + 1))
        keep = np.zeros(n + 1, dtype=bool)
        keep[1:] = sizes >= MIN_BLOB_AREA
        cleaned = keep[labeled]

    out = np.where(cleaned, 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode="L")
