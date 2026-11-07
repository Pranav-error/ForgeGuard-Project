"""Synthetic signature triplets -- stand-in for CEDAR/BHSig260/GPDS (NFR-5, NFR-10).

A "signer style" is a fixed set of stroke control points derived from a seed;
a genuine sample re-renders that style with small jitter (natural variation
between two genuine signings), an impostor sample uses a different style
entirely. This is a genuine-vs-impostor proxy, not skilled forgery.

# ponytail: synthetic strokes only; swap in CEDAR/BHSig260 (papers [1]-[17])
# before trusting reported EER/accuracy.
"""
import random

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch.utils.data import Dataset

SIZE = 128
N_STROKES = 3
PTS_PER_STROKE = 6
JITTER = 2.0


def _style_strokes(seed: int) -> list[list[tuple[float, float]]]:
    rng = random.Random(seed)
    strokes = []
    for s in range(N_STROKES):
        x = rng.uniform(8, 20) + s * (SIZE - 30) / N_STROKES
        y = rng.uniform(SIZE * 0.35, SIZE * 0.65)
        pts = [(x, y)]
        for _ in range(PTS_PER_STROKE):
            x += rng.uniform(4, 12)
            y += rng.uniform(-18, 18)
            x = min(max(x, 2), SIZE - 2)
            y = min(max(y, 2), SIZE - 2)
            pts.append((x, y))
        strokes.append(pts)
    return strokes


def _render(strokes: list[list[tuple[float, float]]], jitter: float, rng: random.Random) -> Image.Image:
    img = Image.new("L", (SIZE, SIZE), 255)
    draw = ImageDraw.Draw(img)
    for pts in strokes:
        jittered = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)) for x, y in pts]
        draw.line(jittered, fill=0, width=2, joint="curve")
    return img


def render_style_sample(style_seed: int, sample_seed: int) -> Image.Image:
    """Public helper: one rendered sample of a given signer style (used by test_module.py)."""
    strokes = _style_strokes(style_seed)
    return _render(strokes, JITTER, random.Random(sample_seed))


def _to_tensor(img: Image.Image) -> torch.Tensor:
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


class SignatureTripletDataset(Dataset):
    """length triplets (anchor, positive, negative), reproducible via seed + idx."""

    def __init__(self, length: int = 512, seed: int = 0):
        self.length, self.seed = length, seed

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, idx: int):
        base = self.seed * 100_000 + idx
        style_a = base * 3
        style_b = base * 3 + 1  # different signer
        anchor = render_style_sample(style_a, base * 7)
        positive = render_style_sample(style_a, base * 7 + 1)
        negative = render_style_sample(style_b, base * 7 + 2)
        return _to_tensor(anchor), _to_tensor(positive), _to_tensor(negative)
