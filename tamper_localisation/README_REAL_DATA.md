# Real-data fine-tuning (Phase 2)

## Why

Live-tested bug (not from the Literature Survey): `SyntheticTamperDataset._make_document`
renders a document as a flat page filling the *entire* frame -- no background, no camera
angle, no lighting, no physical card. A real phone photo of a laminated, lanyard-mounted
REVA University ID card is wildly out-of-distribution for a model trained only on that
generator: tested live, it put tamper confidence at 100/100 across 95% of the frame on a
genuine card (see `ForgeGuard_Phase1_Report.docx`, Section 4.3, bugs 6-7, and the bug table
in `tamper_localisation/real_data.py`'s module docstring).

## What was added

Real data from **SIDTD** (Oriol Ramos Terrades et al., built on **MIDV-2020**: Bulatov et al.,
"MIDV-2020: A Comprehensive Benchmark Dataset for Identity Document Analysis", arXiv:2107.00396).
Dataset homepage: https://tc11.cvc.uab.es/datasets/SIDTD_1/ — downloaded directly from
`http://datasets.cvc.uab.es/SIDTD/` (public, no auth required), not redistributed in this repo.

Two subsets, pulled with `remotezip` so only the needed entries are fetched (not the full
1.3GB / 23GB archives):

- **`templates/` (flat, pixel-aligned real/fake pairs).** 220 forged mock-ID images + their
  unforged source images, real security-pattern textures/fonts/photo layout the old generator
  never had. The real/fake pair is pixel-aligned (same template, one field edited), so a
  thresholded pixel diff *is* an accurate ground-truth tamper mask -- no manual annotation
  (`_diff_mask` in `real_data.py`). These are then composited onto a synthetic background with
  perspective warp + glare (`compose_on_background`) to teach "tampered *and* photographed".
- **`clips/Images/reals/` (actual camera photos).** ~260 real video frames of printed mock
  documents on real backgrounds, at real angles, under real light (MIDV-2020's "clips").
  Genuine, so mask is all-zero -- this is the direct fix: the model had never seen a genuine
  example that looked photographed, only flat synthetic pages, so anything photographed read
  as anomalous.

## Reproducing

Run everything with `-m` from the project root (matching `tamper_localisation.train`'s own
convention) -- running these as bare scripts (`python3 scripts/fetch_sidtd.py`) fails with
`ModuleNotFoundError: No module named 'tamper_localisation'`, since only `-m` puts the project
root on `sys.path`.

```bash
pip install remotezip
python3 -m scripts.fetch_sidtd        # populates data/sidtd/{reals,fakes,clips_reals}/, manifest.json
python3 -m tamper_localisation.train --real-data --epochs 8 --steps-per-epoch 40 --out tamper_checkpoint.pt
python3 -m scripts.eval_real_data tamper_checkpoint.pt --photo path/to/a/real/photo.jpg
```

`data/sidtd/` is gitignored (real third-party images, not ours to redistribute) -- regenerate
it with the fetch script rather than committing it.

## Known remaining limits

- `templates/` images are still flat renders (no background) before compositing; the
  background/perspective/glare around them is still synthetic, not a real photographed scene.
  `clips/` IS real-world, but only as genuine (zero-mask) examples -- we don't have pixel-level
  fake masks for the clips subset (only a coarse whole-card `doc_quad`, too imprecise to use
  as ground truth without overestimating the tampered area), so real-world *tampered* photos
  aren't directly represented, only real-world *genuine* ones plus synthetically-photographed
  tampered ones.
- All source documents are non-Indian ID cards (Albanian, Spanish, Estonian, etc. -- whatever
  SIDTD/MIDV-2020 ships); REVA's own card layout is still unseen by name, only generically
  closer in physical presentation.
- 20 manifest entries are held out from training for `eval_real_data.py`'s IoU check; this is
  a sanity check, not a rigorous train/val/test split with multiple seeds.
