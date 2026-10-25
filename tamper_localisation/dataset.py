"""Synthetic tamper dataset -- stand-in for FSD / real scans (NFR-5, NFR-10).

The Literature Survey Report (Gap 3, Gap 7) notes that document-level
tamper benchmarks are scarce and that small/imbalanced datasets are a
recurring problem. Until the FSD dataset (paper [29]) or real scans are
available, this generator produces document-like pages with a randomly
spliced patch and a pixel-accurate ground-truth mask, with augmentation
for rotation, blur, noise and JPEG recompression (print-scan stand-in).

# ponytail: synthetic only, splice-style tamper; swap in FSD / real scans
# (and inpainting-style tamper) before trusting reported metrics.
"""
import io
import random

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFilter
from torch.utils.data import Dataset

from .preprocess import preprocess


def _make_document(size: int, rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (size, size), (250, 250, 248))
    draw = ImageDraw.Draw(img)
    y = 20
    while y < size - 20:
        x0 = rng.randint(15, 40)
        x1 = rng.randint(size - 60, size - 15)
        shade = rng.randint(40, 90)
        draw.line([(x0, y), (x1, y)], fill=(shade, shade, shade), width=rng.randint(2, 4))
        y += rng.randint(14, 24)
    return img


def _splice_patch(img: Image.Image, rng: random.Random) -> tuple[Image.Image, np.ndarray]:
    size = img.size[0]
    pw, ph = rng.randint(size // 8, size // 3), rng.randint(size // 8, size // 3)
    px, py = rng.randint(0, size - pw), rng.randint(0, size - ph)
    patch = Image.new("RGB", (pw, ph), tuple(rng.randint(0, 255) for _ in range(3)))
    out = img.copy()
    out.paste(patch, (px, py))
    mask = np.zeros((size, size), dtype=np.float32)
    mask[py : py + ph, px : px + pw] = 1.0
    return out, mask


def _augment(img: Image.Image, mask: np.ndarray, rng: random.Random) -> tuple[Image.Image, np.ndarray]:
    angle = rng.uniform(-3, 3)
    img = img.rotate(angle, resample=Image.BILINEAR, fillcolor=(255, 255, 255))
    mask_img = Image.fromarray((mask * 255).astype(np.uint8)).rotate(angle, resample=Image.NEAREST, fillcolor=0)
    mask = np.asarray(mask_img, dtype=np.float32) / 255.0
    if rng.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0, 1.2)))
    if rng.random() < 0.5:
        arr = np.asarray(img, dtype=np.float32)
        arr += rng.uniform(0, 8) * np.random.randn(*arr.shape)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if rng.random() < 0.5:  # print-scan / recompression stand-in
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=rng.randint(55, 85))
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
    return img, mask


class SyntheticTamperDataset(Dataset):
    """`length` samples, generated on the fly and reproducible via `seed + idx`."""

    def __init__(self, length: int = 256, size: int = 256, seed: int = 0, tamper_ratio: float = 0.7):
        self.length, self.size, self.seed, self.tamper_ratio = length, size, seed, tamper_ratio

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, idx: int):
        rng = random.Random(self.seed + idx)
        img = _make_document(self.size, rng)
        if rng.random() < self.tamper_ratio:
            img, mask = _splice_patch(img, rng)
        else:
            mask = np.zeros((self.size, self.size), dtype=np.float32)
        img, mask = _augment(img, mask, rng)
        pre = preprocess(img, size=self.size)
        rgb = torch.from_numpy(pre["rgb"]).float()
        ela = torch.from_numpy(pre["ela"]).float().unsqueeze(0)
        mask_t = torch.from_numpy(mask).float().unsqueeze(0)
        return rgb, ela, mask_t
