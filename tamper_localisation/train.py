"""Training loop for the tamper localiser -- FR-D2, NFR-5.

    python3 -m tamper_localisation.train --epochs 5 --steps-per-epoch 50
"""
import argparse

import torch
from torch.utils.data import DataLoader

from .dataset import SyntheticTamperDataset
from .model import TamperLocaliser


def dice_loss(logits: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.sigmoid(logits)
    inter = (probs * target).sum(dim=(1, 2, 3))
    union = probs.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3))
    return 1 - ((2 * inter + eps) / (union + eps)).mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--steps-per-epoch", type=int, default=50)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--img-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", type=str, default="checkpoint.pt")
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TamperLocaliser(img_size=args.img_size).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    bce = torch.nn.BCEWithLogitsLoss()

    for epoch in range(args.epochs):
        ds = SyntheticTamperDataset(
            length=args.steps_per_epoch * args.batch_size, size=args.img_size, seed=epoch
        )
        loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True)
        total_loss = 0.0
        for rgb, ela, mask in loader:
            rgb, ela, mask = rgb.to(device), ela.to(device), mask.to(device)
            logits = model(rgb, ela)
            loss = bce(logits, mask) + dice_loss(logits, mask)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item()
        print(f"epoch {epoch+1}/{args.epochs}  loss {total_loss/len(loader):.4f}")

    torch.save(model.state_dict(), args.out)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
