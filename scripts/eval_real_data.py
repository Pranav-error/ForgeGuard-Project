"""Before/after real-world generalisation check.

    python3 scripts/eval_real_data.py [checkpoint.pt] [--photo path/to/real_photo.jpg]

Reports: tamper score + flagged-area coverage on a real photo (if given), and pixel IoU
against a held-out slice of SIDTD pairs the training run (with --real-data) never saw.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from tamper_localisation.infer import TamperLocalisationService
from tamper_localisation.real_data import DATA_DIR, _cached_diff_mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", nargs="?", default=None)
    ap.add_argument("--photo", default=None, help="a real-world photo to sanity-check, e.g. a photographed ID card")
    ap.add_argument("--holdout", type=int, default=20, help="must match RealCardDataset's holdout at train time")
    args = ap.parse_args()

    print(f"=== checkpoint: {args.checkpoint or '(untrained / random init)'} ===")
    svc = TamperLocalisationService(checkpoint=args.checkpoint)

    if args.photo and Path(args.photo).exists():
        img = Image.open(args.photo).convert("RGB")
        r = svc.predict(img)
        coverage = (r["heatmap"] >= 0.5).mean()
        print(f"real photo ({args.photo}) -> score={r['score']}  flagged-area={coverage:.3f}  regions={len(r['regions'])}")

    manifest_path = DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        print("no data/sidtd/manifest.json -- run scripts/fetch_sidtd.py first for the held-out IoU check")
        return

    manifest = json.loads(manifest_path.read_text())
    holdout = manifest[-args.holdout:]
    ious = []
    for m in holdout:
        fake_path = DATA_DIR / "fakes" / f"{m['fake']}.jpg"
        if not fake_path.exists():
            continue
        fake_img = Image.open(fake_path).convert("RGB")
        gt = _cached_diff_mask(m["fake"])
        pred = svc.predict(fake_img)
        gt_small = np.asarray(Image.fromarray((gt * 255).astype(np.uint8)).resize((256, 256), Image.NEAREST)) > 127
        pred_mask = pred["heatmap"] >= 0.5
        inter = (gt_small & pred_mask).sum()
        union = (gt_small | pred_mask).sum()
        ious.append(inter / union if union else float("nan"))

    print(f"held-out SIDTD pixel IoU over {len(ious)} pairs: mean={np.nanmean(ious):.4f}")


if __name__ == "__main__":
    main()
