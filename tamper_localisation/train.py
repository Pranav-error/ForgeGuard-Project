"""Training loop for the tamper localiser -- FR-D2, NFR-5.

    python3 -m tamper_localisation.train --epochs 5 --steps-per-epoch 50
"""
import argparse

import torch
from torch.utils.data import ConcatDataset, DataLoader

from .dataset import SyntheticTamperDataset
from .model import TamperLocaliser
from .real_data import RealCardDataset, RealGenuinePhotoDataset


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
    ap.add_argument(
        "--real-data",
        action="store_true",
        help="mix in RealCardDataset + RealGenuinePhotoDataset (data/sidtd/) alongside the "
        "synthetic generator -- see tamper_localisation/real_data.py",
    )
    ap.add_argument("--init-checkpoint", type=str, default=None, help="continue training from this checkpoint instead of random init")
    ap.add_argument(
        "--pos-weight", type=float, default=1.0,
        help="BCEWithLogitsLoss pos_weight -- real tamper regions cover <1%% of pixels "
        "(vs. the synthetic generator's much larger splice patches), so the plain BCE+Dice "
        "loss that works for synthetic data lets the model collapse to 'predict background "
        "everywhere' on sparse real masks. >1 upweights the rare positive-pixel class.",
    )
    args = ap.parse_args()

    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    model = TamperLocaliser(img_size=args.img_size).to(device)
    if args.init_checkpoint:
        model.load_state_dict(torch.load(args.init_checkpoint, map_location=device))
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    bce = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(args.pos_weight, device=device))

    if args.real_data:
        real_cards = RealCardDataset(size=args.img_size, seed=0)
        real_photos = RealGenuinePhotoDataset(size=args.img_size, seed=0)
        print(f"real data: {len(real_cards)} card examples, {len(real_photos)} genuine photos")

    for epoch in range(args.epochs):
        ds = SyntheticTamperDataset(
            length=args.steps_per_epoch * args.batch_size, size=args.img_size, seed=epoch
        )
        if args.real_data:
            # fresh augmentation draw each epoch (seed=epoch) even though the underlying real
            # images are the same fixed, finite set
            ds = ConcatDataset([
                ds,
                RealCardDataset(size=args.img_size, seed=epoch * 10_000),
                RealGenuinePhotoDataset(size=args.img_size, seed=epoch * 10_000),
            ])
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
