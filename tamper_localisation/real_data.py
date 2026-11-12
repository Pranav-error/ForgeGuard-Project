"""Real-photo domain-randomisation augmentation + the SIDTD-backed real dataset.

Gap found live (not in the Literature Survey): SyntheticTamperDataset's `_make_document`
always fills the *entire* canvas edge-to-edge with a plain off-white page -- it never shows
a document as a physical object sitting on a background, at a camera angle, under a light.
A real phone photo of a laminated, lanyard-mounted ID card (background behind it, perspective,
glare) is wildly out-of-distribution for that generator: tested live, the trained model put
tamper confidence at 100/100 across 95% of the frame on exactly such a photo (see the bug
writeup in ForgeGuard_Phase1_Report.docx, Section 4.3). `compose_on_background` below is the
targeted fix -- it photographs the document, not just renders it.

This module also loads real (not synthetic) ID-template images and real forged counterparts
from the SIDTD dataset (Oriol Ramos Terrades et al., built on MIDV-2020 -- see
README_REAL_DATA.md in this directory for provenance, licensing and how to re-fetch it) --
genuine security-pattern texture, fonts and photo layout that the plain `_make_document`
renderer never had either.
"""
import json
import random
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFilter

from .dataset import _augment  # reuse the existing blur/noise/recompression jitter
from .preprocess import preprocess

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "sidtd"


# ---------------------------------------------------------------- perspective warp (PIL-only)
def _perspective_coeffs(src: list[tuple[float, float]], dst: list[tuple[float, float]]) -> list[float]:
    """Solve for the 8 coefficients Image.transform(PERSPECTIVE) needs, mapping dst -> src
    (PIL's convention). Standard least-squares formulation, no OpenCV."""
    a = []
    for (x, y), (X, Y) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        a.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
    a = np.array(a, dtype=np.float64)
    b = np.array([c for pt in src for c in pt], dtype=np.float64)
    res = np.linalg.solve(a, b)
    return res.tolist()


def _random_quad(w: int, h: int, rng: random.Random, jitter: float) -> list[tuple[float, float]]:
    j = jitter
    return [
        (rng.uniform(0, j) * w, rng.uniform(0, j) * h),
        (w - rng.uniform(0, j) * w, rng.uniform(0, j) * h),
        (w - rng.uniform(0, j) * w, h - rng.uniform(0, j) * h),
        (rng.uniform(0, j) * w, h - rng.uniform(0, j) * h),
    ]


def _warp_coeffs(w: int, h: int, rng: random.Random, jitter: float = 0.12) -> list[float]:
    corners = [(0, 0), (w, 0), (w, h), (0, h)]
    quad = _random_quad(w, h, rng, jitter)
    return _perspective_coeffs(corners, quad)


def _warp(img: Image.Image, coeffs: list[float], resample=Image.BICUBIC, fill=(0, 0, 0, 0)) -> Image.Image:
    return img.transform(img.size, Image.PERSPECTIVE, coeffs, resample=resample, fillcolor=fill)


# ---------------------------------------------------------------- background + lighting
def _random_background(size: int, rng: random.Random) -> Image.Image:
    """A cheap stand-in for 'the desk/table/wall behind the card' -- a smooth colour field
    (low-res random noise upsampled with bilinear interpolation, so it blobs rather than
    speckles), not a real photo. Closes the *geometry* gap (document as object, not full-bleed
    page); a real background-photo corpus would close the rest, see README_REAL_DATA.md."""
    small = max(2, size // 32)
    base_color = np.array([rng.randint(20, 235) for _ in range(3)], dtype=np.float32)
    noise = (np.random.rand(small, small, 3).astype(np.float32) - 0.5) * 60
    arr = np.clip(base_color + noise, 0, 255).astype(np.uint8)
    bg = Image.fromarray(arr, mode="RGB").resize((size, size), Image.BILINEAR)
    return bg.filter(ImageFilter.GaussianBlur(radius=size / 40))


def _add_glare(img: Image.Image, rng: random.Random) -> Image.Image:
    """Elliptical soft specular highlight -- laminated/plastic cards reflect light; our flat
    synthetic renders never did."""
    if rng.random() > 0.6:
        return img
    w, h = img.size
    overlay = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(overlay)
    ex, ey = rng.uniform(0.1, 0.9) * w, rng.uniform(0.1, 0.9) * h
    erx, ery = rng.uniform(0.08, 0.22) * w, rng.uniform(0.05, 0.15) * h
    draw.ellipse([ex - erx, ey - ery, ex + erx, ey + ery], fill=rng.randint(120, 200))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(erx, ery) / 2))
    white = Image.new("RGB", (w, h), (255, 255, 255))
    return Image.composite(white, img, overlay)


def compose_on_background(card: Image.Image, mask: np.ndarray, size: int, rng: random.Random) -> tuple[Image.Image, np.ndarray]:
    """The core fix: place `card` (+ its tamper `mask`) on a background, at an angle, under
    uneven light -- instead of letting the document fill the whole frame flat-on. The mask is
    carried through the exact same resize/warp/paste as the card pixels, via one shared set of
    perspective coefficients, so supervision stays pixel-accurate in the final composed frame."""
    canvas = _random_background(size, rng)
    scale = rng.uniform(0.55, 0.9)
    cw, ch = int(size * scale), int(size * scale * card.height / card.width)
    ch = min(ch, size - 4)

    card_r = card.convert("RGBA").resize((cw, ch), Image.BILINEAR)
    mask_r = Image.fromarray((mask * 255).astype(np.uint8)).resize((cw, ch), Image.NEAREST)

    coeffs = _warp_coeffs(cw, ch, rng, jitter=0.1)
    card_rgba = _warp(card_r, coeffs, resample=Image.BICUBIC, fill=(0, 0, 0, 0))
    mask_warped = _warp(mask_r.convert("RGBA"), coeffs, resample=Image.NEAREST, fill=(0, 0, 0, 0))

    max_x, max_y = size - cw, size - ch
    px, py = rng.randint(0, max(max_x, 0)), rng.randint(0, max(max_y, 0))
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.alpha_composite(card_rgba, (px, py))
    out = canvas_rgba.convert("RGB")

    # mask_r.convert("RGBA") replicates L into R/G/B and sets alpha=255 everywhere, so the
    # *alpha* channel after warping is just the card's silhouette, not the mask values -- the
    # actual 0/255 mask survives in the R channel (and R=0 outside the quad too, from
    # fillcolor's R=0), so that's the one to read back.
    full_mask = Image.new("L", (size, size), 0)
    mask_values = mask_warped.split()[0]
    full_mask.paste(mask_values, (px, py))
    full_mask_arr = (np.asarray(full_mask, dtype=np.float32) / 255.0 > 0.5).astype(np.float32)

    out = _add_glare(out, rng)
    return out, full_mask_arr


# ---------------------------------------------------------------- SIDTD-backed dataset
_DIFF_CAP = 640  # cap before diffing: these images cache for the whole training run (see
# _cached_diff_mask) -- at native res (up to ~2000px) that's ~2.3GB of float32 for 220 masks;
# every downstream consumer resizes to <=256px anyway, so keeping native resolution here buys
# nothing but memory and slower ndimage.label.


def _diff_mask(real: Image.Image, fake: Image.Image, thresh: int = 28) -> np.ndarray:
    """Ground-truth tamper mask for a real/fake template pair: both are the same rendered
    document with one field edited, still pixel-aligned, so a thresholded diff *is* an
    accurate pixel-level mask -- no manual annotation needed. Returns uint8 (0/1)."""
    w, h = fake.size
    scale = min(1.0, _DIFF_CAP / max(w, h))
    size = (max(1, int(w * scale)), max(1, int(h * scale)))
    real_a = np.asarray(real.convert("RGB").resize(size), dtype=np.int16)
    fake_a = np.asarray(fake.convert("RGB").resize(size), dtype=np.int16)
    diff = np.abs(real_a - fake_a).sum(axis=-1)
    mask = (diff > thresh).astype(np.uint8)
    # tiny isolated diff pixels (recompression noise, not an edit) -- drop components < 25px
    from scipy import ndimage
    labeled, n = ndimage.label(mask)
    if n:
        sizes = ndimage.sum(mask, labeled, range(1, n + 1))
        for i, s in enumerate(sizes, start=1):
            if s < 25:
                mask[labeled == i] = 0
    return mask


def _to_tensors(composed, mask, size):
    pre = preprocess(composed, size=size)
    rgb = torch.from_numpy(pre["rgb"]).float()
    ela = torch.from_numpy(pre["ela"]).float().unsqueeze(0)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8)).resize((size, size), Image.NEAREST)
    mask_t = torch.from_numpy(np.asarray(mask_img, dtype=np.float32) / 255.0).float().unsqueeze(0)
    return rgb, ela, mask_t


@lru_cache(maxsize=None)
def _cached_diff_mask(fake_name: str) -> np.ndarray:
    """ndimage.label on a full-resolution diff is the slow part of __getitem__ and the result
    never changes for a given real/fake pair -- compute it once, not once per epoch."""
    manifest = json.loads((DATA_DIR / "manifest.json").read_text())
    entry = next(m for m in manifest if m["fake"] == fake_name)
    real_img = Image.open(DATA_DIR / "reals" / entry["src"]).convert("RGB")
    fake_img = Image.open(DATA_DIR / "fakes" / f"{fake_name}.jpg").convert("RGB")
    return _diff_mask(real_img, fake_img)


class RealCardDataset:
    """Real (not synthetic) ID-template images, composited onto a photographed-looking scene.
    Loads from data/sidtd/ (see README_REAL_DATA.md for how that folder is populated)."""

    def __init__(self, size: int = 256, seed: int = 0, holdout: int = 40, split: str = "train"):
        """`holdout` manifest entries are reserved for evaluate_real_data.py's generalisation
        check and never seen by `split="train"` -- without this, "the model's IoU on SIDTD
        pairs" would just be re-measuring memorised training examples."""
        self.size = size
        self.seed = seed
        manifest_path = DATA_DIR / "manifest.json"
        full_manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
        self.manifest = full_manifest[:-holdout] if split == "train" else full_manifest[-holdout:]
        self.reals = sorted({m["src"] for m in self.manifest})

        # Each item is either a (fake_name, src) tamper example or a (None, src) genuine one,
        # one genuine per unique real image so the model also sees real-but-untampered cards.
        self.items = [(m["fake"], m["src"]) for m in self.manifest] + [(None, r) for r in self.reals]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int):
        rng = random.Random(self.seed + idx)
        fake_name, src = self.items[idx]

        if fake_name is None:
            card = Image.open(DATA_DIR / "reals" / src).convert("RGB")
            mask = np.zeros((card.height, card.width), dtype=np.float32)
        else:
            card = Image.open(DATA_DIR / "fakes" / f"{fake_name}.jpg").convert("RGB")
            mask = _cached_diff_mask(fake_name)

        composed, mask = compose_on_background(card, mask, self.size, rng)
        composed, mask = _augment(composed, mask, rng)
        return _to_tensors(composed, mask, self.size)


class RealGenuinePhotoDataset:
    """Actual camera photos (SIDTD `clips`, built on MIDV-2020) of printed mock documents on
    real backgrounds, at real angles, under real light -- genuine, so mask is all-zero. This is
    the direct fix for the bug that motivated this module: the model had never seen a *genuine*
    example that looked photographed, only flat synthetic pages, so anything photographed read
    as anomalous. No compositing needed; these are already real photos."""

    def __init__(self, size: int = 256, seed: int = 0):
        self.size = size
        self.seed = seed
        self.files = sorted((DATA_DIR / "clips_reals").glob("*.jpg")) if (DATA_DIR / "clips_reals").exists() else []

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int):
        rng = random.Random(self.seed + idx)
        img = Image.open(self.files[idx]).convert("RGB")
        # letterbox into a square instead of a hard resize -- keeps the real aspect/perspective
        # of the photo rather than stretching it
        w, h = img.size
        side = max(w, h)
        canvas = Image.new("RGB", (side, side), (0, 0, 0))
        canvas.paste(img, ((side - w) // 2, (side - h) // 2))
        img = canvas.resize((self.size, self.size), Image.BILINEAR)
        mask = np.zeros((self.size, self.size), dtype=np.float32)
        img, mask = _augment(img, mask, rng)
        return _to_tensors(img, mask, self.size)
