"""Signature region detection -- FR-S1.

# ponytail: heuristic largest-ink-blob detector (no training data available for a
# real object detector yet). Swap for a trained detector (paper [13]'s approach)
# once signature-on-page training data exists; keep the same detect() contract.
"""
import numpy as np
from PIL import Image
from scipy import ndimage

INK_THRESHOLD = 180       # pixels darker than this (0-255 grayscale) count as ink
MIN_AREA = 60              # reject specks; genuine pen strokes are thin, so this stays low --
                           # the aspect filter below is what actually rejects ruled lines
MAX_ASPECT = 8.0           # reject long thin ruled lines (width/height or height/width)
SEARCH_BAND = (0.5, 1.0)   # fraction of page height to search (signatures sit low on a page)


def detect(page: Image.Image) -> dict | None:
    """Return {"bbox": [x, y, w, h]} for the best signature candidate, or None."""
    gray = np.asarray(page.convert("L"), dtype=np.uint8)
    h, w = gray.shape
    y0 = int(h * SEARCH_BAND[0])
    band = gray[y0:, :]

    ink = band < INK_THRESHOLD
    labeled, n = ndimage.label(ink)
    if n == 0:
        return None

    best, best_score = None, -1.0
    slices = ndimage.find_objects(labeled)
    for i, sl in enumerate(slices, start=1):
        ys, xs = sl
        bh, bw = ys.stop - ys.start, xs.stop - xs.start
        area = int((labeled[sl] == i).sum())
        if area < MIN_AREA:
            continue
        aspect = max(bw / max(bh, 1), bh / max(bw, 1))
        if aspect > MAX_ASPECT:
            continue  # looks like a ruled line, not a signature
        # score favours blobs with irregular (non-line) shape and reasonable size
        fill_ratio = area / (bw * bh)
        score = area * fill_ratio
        if score > best_score:
            best_score = score
            best = (int(xs.start), int(ys.start + y0), bw, bh)

    if best is None:
        return None
    return {"bbox": list(best)}
