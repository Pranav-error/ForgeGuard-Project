"""Evaluation -- NFR-5: precision, recall, F1, IoU and AUC, not accuracy alone.

    python3 -m tamper_localisation.evaluate --checkpoint checkpoint.pt --samples 64
"""
import argparse

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader

from .dataset import SyntheticTamperDataset
from .model import TamperLocaliser


def pixel_metrics(probs: np.ndarray, targets: np.ndarray, threshold: float = 0.5) -> dict:
    """Pixel-level precision/recall/F1/IoU/AUC over flattened probability maps."""
    preds = (probs >= threshold).astype(np.uint8)
    targets = targets.astype(np.uint8)
    tp = int(((preds == 1) & (targets == 1)).sum())
    fp = int(((preds == 1) & (targets == 0)).sum())
    fn = int(((preds == 0) & (targets == 1)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0
    auc = roc_auc_score(targets.ravel(), probs.ravel()) if len(np.unique(targets)) > 1 else float("nan")
    return {"precision": precision, "recall": recall, "f1": f1, "iou": iou, "auc": auc}


@torch.no_grad()
def evaluate(model: TamperLocaliser, loader: DataLoader, device: str) -> dict:
    model.eval()
    all_probs, all_targets = [], []
    for rgb, ela, mask in loader:
        rgb, ela = rgb.to(device), ela.to(device)
        probs = torch.sigmoid(model(rgb, ela)).cpu().numpy()
        all_probs.append(probs)
        all_targets.append(mask.numpy())
    probs = np.concatenate(all_probs)
    targets = np.concatenate(all_targets)
    return pixel_metrics(probs, targets)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=str, default=None)
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--img-size", type=int, default=256)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TamperLocaliser(img_size=args.img_size).to(device)
    if args.checkpoint:
        model.load_state_dict(torch.load(args.checkpoint, map_location=device))

    ds = SyntheticTamperDataset(length=args.samples, size=args.img_size, seed=999)
    loader = DataLoader(ds, batch_size=8)
    metrics = evaluate(model, loader, device)
    for k, v in metrics.items():
        print(f"{k:>10}: {v:.4f}")


if __name__ == "__main__":
    main()
