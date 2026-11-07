"""Triplet-loss training for the signature encoder.

    python3 -m signature_verification.train --epochs 5 --steps-per-epoch 50
"""
import argparse

import torch
from torch.utils.data import DataLoader

from .dataset import SignatureTripletDataset
from .encoder import SignatureEncoder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--steps-per-epoch", type=int, default=50)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--margin", type=float, default=0.3)
    ap.add_argument("--out", type=str, default="signature_checkpoint.pt")
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SignatureEncoder().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = torch.nn.TripletMarginLoss(margin=args.margin)

    for epoch in range(args.epochs):
        ds = SignatureTripletDataset(length=args.steps_per_epoch * args.batch_size, seed=epoch)
        loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True)
        total_loss = 0.0
        for a, p, n in loader:
            a, p, n = a.to(device), p.to(device), n.to(device)
            ea, ep, en = model(a), model(p), model(n)
            loss = loss_fn(ea, ep, en)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item()
        print(f"epoch {epoch+1}/{args.epochs}  loss {total_loss/len(loader):.4f}")

    torch.save(model.state_dict(), args.out)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
