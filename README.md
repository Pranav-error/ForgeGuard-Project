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
| `Detailed_Design_Document.pdf` / `.docx` | Class/component breakdown, algorithms, data structures and interface spec for the assigned module (matches `tamper_localisation/` line for line), pseudocode-level design for the remaining services, a message-level sequence diagram, and system-wide error handling. The `.docx` is editable. |
| `ForgeGuard_IEEE_Paper.docx` / `.pdf` | IEEE-format paper draft. |
| `report.html`, `design.html`, `paper.html` | Source HTML for the three documents above. |
| `papers/` | The 52 source papers (PDF) reviewed in the literature survey. |
| `txt/` | Plain-text extractions of each paper in `papers/`. |
| `build.py`, `design_build.py`, `paper_build.py`, `docx_build.py` | Scripts that render the HTML sources to PDF/DOCX via headless Chrome. |
| `tamper_localisation/` | Dual-stream tamper localiser (assigned module) — see below. |
| `signature_verification/` | Signature detection, cleaning and writer-independent metric-learning verification. |
| `ocr_validation/` | OCR (via the `tesseract` binary), field-format checks and the financial arithmetic gate. |
| `fusion/` | Combines the three sub-scores into one authenticity score, label and reason. |
| `api/` | FastAPI orchestrator wiring all four services together, with SQLite persistence, auth/RBAC (NFR-9), an append-only audit log, and a minimal test web page. |

## Building the documents

Each `*_build.py` script fills placeholders (name, USN, date, etc.) in its matching `.html` file
and prints it to PDF with headless Chrome:

```bash
python3 build.py             # -> Literature_Survey_Report.pdf
python3 objectives_build.py       # -> Project_Objectives.pdf
python3 objectives_docx_build.py  # -> Project_Objectives.docx (editable, run after objectives_build.py)
python3 design_build.py      # -> System_Design_Document.pdf
python3 design_docx_build.py # -> System_Design_Document.docx (editable, run after design_build.py)
python3 detailed_design_build.py      # -> Detailed_Design_Document.pdf
python3 detailed_design_docx_build.py # -> Detailed_Design_Document.docx (editable, run after detailed_design_build.py)
python3 paper_build.py       # -> ForgeGuard_IEEE_Paper.pdf
python3 docx_build.py        # -> ForgeGuard_IEEE_Paper.docx
```

Requires Google Chrome installed at the default macOS path.

## Running the full system

All four services (tamper localisation, signature verification, OCR/field validation, fusion)
plus the orchestrator API are implemented and working end to end.

```bash
pip install -r requirements.txt      # torch, fastapi, uvicorn, etc.
brew install tesseract               # OCR binary, shelled out to directly

# self-check each service (no dataset needed for any of them)
python3 -m tamper_localisation.test_module
python3 -m signature_verification.test_module
python3 -m ocr_validation.test_module
python3 -m fusion.test_module

# run the API
uvicorn api.main:app --reload
# open http://127.0.0.1:8000 -- register an account, log in, register a reference
# signature, then upload a document (the page handles the bearer token for you)

# bootstrap an admin account (self-registration only ever creates "verifier")
python3 -m api.create_admin admin@example.com somepassword
```

`POST /auth/register` / `POST /auth/login` (NFR-9): every other route requires
`Authorization: Bearer <token>` from login, and `/admin/*` routes additionally require the
`admin` role (403 otherwise). `POST /signatures` registers a reference signature for a signer;
`POST /documents` runs the full pipeline (preprocess → signature/tamper/OCR in sequence → fusion
→ persist) and returns the score, label, reason, sub-scores and a heatmap overlay URL;
`GET /documents/{id}/verification` re-fetches a past result from SQLite; `GET /admin/audit-log`
lists the append-only audit trail (NFR-8). If a detector fails or a signer has no registered
reference, the orchestrator degrades gracefully (that sub-score is recorded as missing and the
label is capped below Genuine) instead of failing the request — see `api/orchestrator.py`.

Training and evaluation for the two learned models (`tamper_localisation`, `signature_verification`)
currently run against synthetic data generators — stand-ins for the FSD dataset (paper [29]) and
CEDAR/BHSig260 (papers [1]–[17]) respectively, until real labelled data is available. Reported
metrics should not be trusted as final numbers until trained on real data (see the `ponytail:`
notes in each module's `dataset.py`). The OCR, fusion, API and persistence layers run against real
inputs (actual Tesseract OCR, actual SQLite writes) with no synthetic stand-in.

## Status

Phase 1 (this repo): all four services implemented and wired end to end through a working API
(tamper localisation, signature verification, OCR/field validation, fusion and scoring), with
SQLite persistence, an append-only audit log, and auth/RBAC (NFR-9). Not yet built: a
non-minimal web client and real training data for the two learned models.

Phase 2 (future work): blockchain anchoring of the stored document hash, and an anomaly-detection
worker for forgery types outside the training distribution — both designed to slot in behind the
existing replaceable-detector interface without changing the orchestrator or API.

## License

The papers under `papers/` and `txt/` are included for reference as part of the literature survey
and remain the copyright of their respective publishers (IEEE and others) — they are not covered
by any license on this repository's own content.
