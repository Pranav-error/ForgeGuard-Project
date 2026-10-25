# ForgeGuard

An AI-based document forgery detection and verification system. ForgeGuard accepts a scanned or
photographed document — an identity card, certificate, transcript, invoice or signed legal page —
and decides whether it is genuine or forged by combining:

- **Tamper localisation** — a dual-stream (SRM noise-residual + semantic RGB) encoder-decoder that
  outputs a pixel-level heatmap of edited regions.
- **Signature verification** — detects and cleans the signature region, then compares it against
  1–5 stored reference signatures with a writer-independent similarity model.
- **OCR / field validation** — extracts text, checks field formats, and (for financial documents)
  verifies arithmetic consistency.
- **Fusion & scoring** — combines the three sub-scores into one 0–100 authenticity score with a
  label (Genuine / Suspicious / Forged) and a plain-language explanation.

This is a college major project (REVA University, School of Computer Science & Engineering).

## Repository contents

| File | Description |
|---|---|
| `Literature_Survey_Report.pdf` | Survey of 52 IEEE papers (2018–2026) across four themes — signature verification, image tampering localisation, document/financial/legal forgery detection, and blockchain-anchored credential verification — with 9 literature gaps and the functional/non-functional requirements derived from them. |
| `Project_Objectives.pdf` / `.docx` | Objectives O1–O9, one per literature gap, each traced to the requirement IDs it is implemented through. The `.docx` is editable. |
| `System_Design_Document.pdf` / `.docx` | Architecture, per-module design, data schema, API design, and the NFR-to-design-decision mapping — implements objectives O1–O9. The `.docx` is editable. |
| `ForgeGuard_IEEE_Paper.docx` / `.pdf` | IEEE-format paper draft. |
| `report.html`, `design.html`, `paper.html` | Source HTML for the three documents above. |
| `papers/` | The 52 source papers (PDF) reviewed in the literature survey. |
| `txt/` | Plain-text extractions of each paper in `papers/`. |
| `build.py`, `design_build.py`, `paper_build.py`, `docx_build.py` | Scripts that render the HTML sources to PDF/DOCX via headless Chrome. |
| `tamper_localisation/` | Prototype implementation of the assigned module (dual-stream tamper localiser) — see below. |

## Building the documents

Each `*_build.py` script fills placeholders (name, USN, date, etc.) in its matching `.html` file
and prints it to PDF with headless Chrome:

```bash
python3 build.py             # -> Literature_Survey_Report.pdf
python3 objectives_build.py       # -> Project_Objectives.pdf
python3 objectives_docx_build.py  # -> Project_Objectives.docx (editable, run after objectives_build.py)
python3 design_build.py      # -> System_Design_Document.pdf
python3 design_docx_build.py # -> System_Design_Document.docx (editable, run after design_build.py)
python3 paper_build.py       # -> ForgeGuard_IEEE_Paper.pdf
python3 docx_build.py        # -> ForgeGuard_IEEE_Paper.docx
```

Requires Google Chrome installed at the default macOS path.

## Tamper Localisation Module (assigned module — FR-D1, FR-D2, FR-D6)

`tamper_localisation/` is a working prototype of the assigned module from the System Design
Document: a dual-stream (fixed SRM noise-residual + semantic RGB) encoder-decoder behind one
fixed interface, `TamperLocalisationService.predict(image)`, returning a pixel mask, heatmap,
0–100 tamper sub-score and the largest suspicious regions with coordinates.

```bash
pip install -r tamper_localisation/requirements.txt
python3 -m tamper_localisation.test_module              # self-check (no dataset needed)
python3 -m tamper_localisation.train --epochs 5 --out checkpoint.pt
python3 -m tamper_localisation.evaluate --checkpoint checkpoint.pt   # precision/recall/F1/IoU/AUC, NFR-5
```

Training and evaluation currently run against `dataset.py`'s synthetic splice generator, a
stand-in for the FSD dataset (paper [29]) until real document scans are available — reported
metrics should not be trusted as final numbers until trained on that data (see the `ponytail:`
note in `dataset.py`).

## Status

Phase 1 (this repo): tamper localisation (prototype implemented), signature verification,
OCR/field validation, fusion and scoring, and an audit log.

Phase 2 (future work): blockchain anchoring of the stored document hash, and an anomaly-detection
worker for forgery types outside the training distribution — both designed to slot in behind the
existing replaceable-detector interface without changing the orchestrator or API.

## License

The papers under `papers/` and `txt/` are included for reference as part of the literature survey
and remain the copyright of their respective publishers (IEEE and others) — they are not covered
by any license on this repository's own content.
