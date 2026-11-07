"""Evaluation -- NFR-5: equal error rate (EER) and accuracy at the EER threshold.

    python3 -m signature_verification.evaluate --checkpoint signature_checkpoint.pt --samples 200
"""
import argparse

import numpy as np
import torch
from torch.utils.data import DataLoader

from .dataset import SignatureTripletDataset
from .encoder import SignatureEncoder


def compute_eer(genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> dict:
    thresholds = np.linspace(0, 1, 201)
    far = np.array([(impostor_scores >= t).mean() for t in thresholds])
    frr = np.array([(genuine_scores < t).mean() for t in thresholds])
    idx = np.argmin(np.abs(far - frr))
    eer = (far[idx] + frr[idx]) / 2
    threshold = thresholds[idx]
    accuracy = ((genuine_scores >= threshold).sum() + (impostor_scores < threshold).sum()) / (
        len(genuine_scores) + len(impostor_scores)
    )
    return {"eer": float(eer), "threshold": float(threshold), "accuracy": float(accuracy)}


@torch.no_grad()
def evaluate(model: SignatureEncoder, loader: DataLoader, device: str) -> dict:
    model.eval()
    genuine, impostor = [], []
    for a, p, n in loader:
        a, p, n = a.to(device), p.to(device), n.to(device)
        ea, ep, en = model(a), model(p), model(n)
        genuine.append((ea * ep).sum(dim=1).cpu().numpy())
        impostor.append((ea * en).sum(dim=1).cpu().numpy())
    return compute_eer(np.concatenate(genuine), np.concatenate(impostor))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=str, default=None)
    ap.add_argument("--samples", type=int, default=200)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SignatureEncoder().to(device)
    if args.checkpoint:
        model.load_state_dict(torch.load(args.checkpoint, map_location=device))

    ds = SignatureTripletDataset(length=args.samples, seed=999)
    loader = DataLoader(ds, batch_size=16)
    metrics = evaluate(model, loader, device)
    for k, v in metrics.items():
        print(f"{k:>10}: {v:.4f}")


if __name__ == "__main__":
    main()
