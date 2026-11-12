"""Before/after real-world generalisation check.

    python3 -m scripts.eval_real_data [checkpoint.pt] [--photo path/to/real_photo.jpg]

Reports: tamper score + flagged-area coverage on a real photo (if given), and pixel IoU
against a held-out slice of SIDTD pairs the training run (with --real-data) never saw --
overall and broken down by forgery type (Crop_and_Replace vs. Inpaint_and_Rewrite), since
they're visually different tasks and an overall average can hide one failing completely.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from tamper_localisation.infer import TamperLocalisationService
from tamper_localisation.real_data import DATA_DIR, _cached_diff_mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", nargs="?", default=None)
    ap.add_argument("--photo", default=None, help="a real-world photo to sanity-check, e.g. a photographed ID card")
    ap.add_argument("--holdout", type=int, default=40, help="must match RealCardDataset's holdout at train time")
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
        print("no data/sidtd/manifest.json -- run `python3 -m scripts.fetch_sidtd` first for the held-out IoU check")
        return

    manifest = json.loads(manifest_path.read_text())
    holdout = manifest[-args.holdout:]
    by_ctype = defaultdict(list)
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
        iou = inter / union if union else float("nan")
        by_ctype[m.get("ctype") or "unknown"].append(iou)

    all_ious = [v for vs in by_ctype.values() for v in vs]
    print(f"held-out SIDTD pixel IoU over {len(all_ious)} pairs: mean={np.nanmean(all_ious):.4f}")
    for ctype, ious in sorted(by_ctype.items()):
        print(f"  {ctype:<20} n={len(ious):<4} mean IoU={np.nanmean(ious):.4f}")


if __name__ == "__main__":
    main()
