"""Genuine-only document generator -- the autoencoder never sees a forged example.

# ponytail: synthetic "documents" (gray ruled lines on a page), same stand-in
# as tamper_localisation's generator until real genuine scans are available.
# Deliberately not importing tamper_localisation.dataset's private helpers --
# this module should stay independent so a real anomaly-detection dataset can
# replace it without touching the tamper module (NFR-7).
"""
import random

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFilter
from torch.utils.data import Dataset

SIZE = 128


def _make_genuine_page(size: int, rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (size, size), (250, 250, 248))
    draw = ImageDraw.Draw(img)
    y = size // 12
    while y < size - size // 12:
        x0 = rng.randint(size // 15, size // 8)
        x1 = rng.randint(size - size // 4, size - size // 15)
        shade = rng.randint(40, 90)
        draw.line([(x0, y), (x1, y)], fill=(shade, shade, shade), width=1)
        y += rng.randint(size // 20, size // 12)
    if rng.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0, 0.8)))
    return img


class GenuineDocumentDataset(Dataset):
    def __init__(self, length: int = 512, size: int = SIZE, seed: int = 0):
        self.length, self.size, self.seed = length, size, seed

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, idx: int) -> torch.Tensor:
        rng = random.Random(self.seed * 100_000 + idx)
        img = _make_genuine_page(self.size, rng)
        arr = np.asarray(img, dtype=np.float32) / 255.0
        return torch.from_numpy(arr).permute(2, 0, 1)
