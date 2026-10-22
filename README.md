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
| `Project_Objectives.pdf` | Objectives O1–O9, one per literature gap, each traced to the requirement IDs it is implemented through. |
| `System_Design_Document.pdf` | Architecture, per-module design, data schema, API design, and the NFR-to-design-decision mapping — implements objectives O1–O9. |
| `ForgeGuard_IEEE_Paper.docx` / `.pdf` | IEEE-format paper draft. |
| `report.html`, `design.html`, `paper.html` | Source HTML for the three documents above. |
| `papers/` | The 52 source papers (PDF) reviewed in the literature survey. |
| `txt/` | Plain-text extractions of each paper in `papers/`. |
| `build.py`, `design_build.py`, `paper_build.py`, `docx_build.py` | Scripts that render the HTML sources to PDF/DOCX via headless Chrome. |

## Building the documents

Each `*_build.py` script fills placeholders (name, USN, date, etc.) in its matching `.html` file
and prints it to PDF with headless Chrome:

```bash
python3 build.py             # -> Literature_Survey_Report.pdf
python3 objectives_build.py  # -> Project_Objectives.pdf
python3 design_build.py      # -> System_Design_Document.pdf
python3 paper_build.py       # -> ForgeGuard_IEEE_Paper.pdf
python3 docx_build.py        # -> ForgeGuard_IEEE_Paper.docx
```

Requires Google Chrome installed at the default macOS path.

## Status

Phase 1 (this repo): tamper localisation, signature verification, OCR/field validation, fusion
and scoring, and an audit log.

Phase 2 (future work): blockchain anchoring of the stored document hash, and an anomaly-detection
worker for forgery types outside the training distribution — both designed to slot in behind the
existing replaceable-detector interface without changing the orchestrator or API.

## License

The papers under `papers/` and `txt/` are included for reference as part of the literature survey
and remain the copyright of their respective publishers (IEEE and others) — they are not covered
by any license on this repository's own content.
