"""Evaluation -- NFR-5, and the Gap-8 claim itself: does reconstruction error
separate genuine pages from a forgery type the autoencoder never trained on?

Genuine pages come from this module's own generator; "anomalous" pages reuse
tamper_localisation's splice generator purely as an unseen-forgery-type stand-in
for evaluation -- the autoencoder is never trained on them.

    python3 -m anomaly_detection.evaluate --checkpoint anomaly_checkpoint.pt --samples 100
"""
import argparse
import random

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

from tamper_localisation.dataset import _make_document, _splice_patch

from .dataset import GenuineDocumentDataset, SIZE
from .model import ConvAutoencoder


@torch.no_grad()
def reconstruction_errors(model: ConvAutoencoder, images: torch.Tensor, device: str) -> np.ndarray:
    images = images.to(device)
    recon = model(images)
    return ((recon - images) ** 2).mean(dim=(1, 2, 3)).cpu().numpy()


def _anomalous_batch(n: int, size: int, seed: int) -> torch.Tensor:
    imgs = []
    for i in range(n):
        rng = random.Random(seed * 1000 + i)
        base = _make_document(size, rng)
        spliced, _mask = _splice_patch(base, rng)
        arr = np.asarray(spliced, dtype=np.float32) / 255.0
        imgs.append(torch.from_numpy(arr).permute(2, 0, 1))
    return torch.stack(imgs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=str, default=None)
    ap.add_argument("--samples", type=int, default=100)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ConvAutoencoder().to(device)
    if args.checkpoint:
        model.load_state_dict(torch.load(args.checkpoint, map_location=device))
    model.eval()

    genuine_ds = GenuineDocumentDataset(length=args.samples, size=SIZE, seed=999)
    genuine_batch = torch.stack([genuine_ds[i] for i in range(len(genuine_ds))])
    genuine_err = reconstruction_errors(model, genuine_batch, device)

    anomalous_batch = _anomalous_batch(args.samples, SIZE, seed=999)
    anomalous_err = reconstruction_errors(model, anomalous_batch, device)

    labels = np.concatenate([np.zeros(len(genuine_err)), np.ones(len(anomalous_err))])
    scores = np.concatenate([genuine_err, anomalous_err])
    auc = roc_auc_score(labels, scores)

    threshold = float(genuine_err.mean() + 2 * genuine_err.std())
    print(f"genuine error   mean={genuine_err.mean():.5f} std={genuine_err.std():.5f}")
    print(f"anomalous error mean={anomalous_err.mean():.5f} std={anomalous_err.std():.5f}")
    print(f"       auc: {auc:.4f}")
    print(f" threshold: {threshold:.5f}   (mean + 2*std of genuine error; use as AnomalyDetectionService(threshold=...))")


if __name__ == "__main__":
    main()
