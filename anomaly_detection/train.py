"""Train the autoencoder on genuine documents only.

    python3 -m anomaly_detection.train --epochs 10 --steps-per-epoch 50
"""
import argparse

import torch
from torch.utils.data import DataLoader

from .dataset import GenuineDocumentDataset
from .model import ConvAutoencoder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--steps-per-epoch", type=int, default=50)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", type=str, default="anomaly_checkpoint.pt")
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ConvAutoencoder().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = torch.nn.MSELoss()

    for epoch in range(args.epochs):
        ds = GenuineDocumentDataset(length=args.steps_per_epoch * args.batch_size, seed=epoch)
        loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True)
        total_loss = 0.0
        for x in loader:
            x = x.to(device)
            recon = model(x)
            loss = loss_fn(recon, x)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item()
        print(f"epoch {epoch+1}/{args.epochs}  loss {total_loss/len(loader):.5f}")

    torch.save(model.state_dict(), args.out)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
