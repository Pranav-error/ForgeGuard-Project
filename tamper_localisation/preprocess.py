"""Pre-processing pipeline for the tamper-localisation module -- FR-D1.

Deskew, resize/normalise, and compute the ELA map used as a supporting
signal alongside the SRM stream (Gap 4 of the Literature Survey Report:
ELA/compression cues alone are not enough, so they are one channel among
several, not the sole signal).
"""
import io

import numpy as np
from PIL import Image, ImageChops


def deskew(img: Image.Image, max_angle: float = 10.0, step: float = 1.0) -> Image.Image:
    """Rotate to the angle that minimises the variance of row-wise ink density.

    Cheap stand-in for a Hough-line deskew: good enough for small scan tilts
    and needs no extra dependency (no OpenCV).
    """
    gray = np.asarray(img.convert("L"), dtype=np.float32)
    best_angle, best_score = 0.0, -1.0
    angle = -max_angle
    while angle <= max_angle:
        rotated = np.asarray(img.convert("L").rotate(angle, resample=Image.BILINEAR, fillcolor=255), dtype=np.float32)
        row_sums = rotated.sum(axis=1)
        score = row_sums.var()
        if score > best_score:
            best_score, best_angle = score, angle
        angle += step
    return img.rotate(best_angle, resample=Image.BICUBIC, fillcolor=(255, 255, 255)) if img.mode == "RGB" else img.rotate(best_angle)


def resize_and_normalise(img: Image.Image, size: int = 256) -> np.ndarray:
    """Resize to size x size and scale to [0, 1], shape (3, H, W)."""
    img = img.convert("RGB").resize((size, size), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.transpose(arr, (2, 0, 1))


def compute_ela(img: Image.Image, quality: int = 90) -> np.ndarray:
    """Error Level Analysis: re-save at `quality` and diff against the original."""
    img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    buf.seek(0)
    resaved = Image.open(buf)
    diff = ImageChops.difference(img, resaved)
    arr = np.asarray(diff, dtype=np.float32)
    arr = arr / (arr.max() + 1e-6)
    return arr.mean(axis=2)  # (H, W), single channel


def preprocess(img: Image.Image, size: int = 256) -> dict:
    """Full FR-D1 pipeline: deskew, resize/normalise, SRM-ready RGB tensor, ELA map."""
    img = deskew(img)
    rgb = resize_and_normalise(img, size)
    ela = compute_ela(img.resize((size, size), Image.BILINEAR))
    return {"rgb": rgb, "ela": ela}
