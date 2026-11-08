# ForgeGuard

**ForgeGuard** is an AI-based document forgery detection and verification system. It accepts a
scanned or photographed document — an identity card, academic certificate, transcript, invoice,
bank statement, or signed legal page — and returns an explainable, evidence-based authenticity
decision: a 0–100 score, a label (**Genuine / Suspicious / Forged**), a plain-language reason, a
visual heatmap of any tampered region, and a tamper-evident record that the decision itself was
never altered after the fact.

It is a college major project (REVA University, School of Computer Science & Engineering,
REVA Internship Opportunities program), built around five independent evidence sources combined
by one fusion stage, rather than a single end-to-end classifier — a design decision made directly
in response to gaps found in a 52-paper literature survey (see [Project documents](#project-documents)
below). **Both phases of the project plan are complete**: every service described in the design
documents is implemented, trained, tested, and verified working end to end through a real REST API.

---

## Table of contents

- [What ForgeGuard does](#what-forgeguard-does)
- [Architecture](#architecture)
- [Project documents](#project-documents)
- [Repository layout](#repository-layout)
- [The five services, in detail](#the-five-services-in-detail)
  1. [Tamper Detection and Localisation](#1-tamper-detection-and-localisation-tamper_localisation)
  2. [Signature Verification](#2-signature-verification-signature_verification)
  3. [OCR / Field Validation](#3-ocr--field-validation-ocr_validation)
  4. [Anomaly Detection (Phase 2)](#4-anomaly-detection-phase-2-anomaly_detection)
  5. [Fusion & Scoring](#5-fusion--scoring-fusion)
- [The Ledger (Phase 2 — blockchain-style anchoring)](#the-ledger-phase-2--blockchain-style-anchoring-ledger)
- [The Orchestrator and API (`api/`)](#the-orchestrator-and-api-api)
- [Data design](#data-design)
- [Setup and running the system](#setup-and-running-the-system)
- [Training results](#training-results)
- [Testing](#testing)
- [What's real vs. what's a documented stand-in](#whats-real-vs-whats-a-documented-stand-in)
- [Status](#status)
- [License](#license)

---

## What ForgeGuard does

A forged document often looks entirely normal to a human reviewer while carrying one altered
field — a date, a grade, a total, a pasted signature. Manual verification is slow, inconsistent,
and a single missed forgery can cause real financial or legal harm. ForgeGuard automates this by
combining four independent checks, because the literature survey found that no single technique
catches every forgery type:

1. **Is the page itself edited?** A dual-stream neural network looks for pixel-level tampering —
   splicing, copy-move, inpainting — using both noise-residual and semantic visual cues.
2. **Is the signature genuine?** A metric-learning model compares the signature on the page
   against stored reference signatures for the claimed signer.
3. **Do the text fields make sense?** OCR extracts the text; field-format rules and (for financial
   documents) an arithmetic check look for inconsistencies.
4. **Does the page look like a forgery type nobody trained the model on?** An autoencoder trained
   only on genuine documents flags pages that reconstruct poorly — a safety net for forgery types
   outside the other three checks' training distribution.

A fifth stage, **fusion**, combines all available evidence into one score, label, and reason —
never reaching "Genuine" if any check is missing — and every verification is written to an
append-only audit log and **anchored on a local hash-chain ledger**, so a later attempt to alter a
past decision in the database is cryptographically detectable.

## Architecture

```
                         Client (web page / any HTTP client)
                                     |
                              API Gateway (auth, RBAC)
                                     |
                        Verification Orchestrator (api/orchestrator.py)
                     /        |             |              \
          Signature      Tamper         OCR / Field      Anomaly
          Verification   Localisation   Validation       Detection
          (writer-ind.   (SRM + RGB     (Tesseract +     (autoencoder,
           metric         dual-stream    regex rules +    genuine-only
           learning)      U-Net-style)   arithmetic       training)
                \              |         gate)           /
                 \             |             |          /
                  \____________|_____________|_________/
                               |
                      Fusion & Scoring (fusion/)
                     (weighted score, label, reason)
                               |
              ____________________________________
             |                                     |
     SQLite persistence                    Ledger (hash-chain anchor)
  (documents, verifications,              (every verification's document
   signatures, audit_log)                  hash becomes a tamper-evident
                                            block)
```

Every detector sits behind one fixed interface — image in, a small evidence dict out — so any one
of them can be replaced (a better model, a different algorithm, a real pretrained network once
labelled data exists) without touching the orchestrator, the API, or any other detector. This was
a deliberate response to a literature gap (Gap 8: supervised models only catch forgery types they
were trained on) and is the same property that let the anomaly detector and the ledger be added in
Phase 2 without changing a single line of the Phase 1 orchestrator's detector-calling logic beyond
adding one more call.

## Project documents

The project followed a four-stage design process before any service was implemented; each
document is both a PDF/DOCX deliverable and traceable, identifier-for-identifier, into the next:

| Document | Contents |
|---|---|
| **`Literature_Survey_Report.pdf`** | A survey of 52 IEEE papers (2018–2026) across four themes — signature verification, image tampering localisation, document/financial/legal forgery detection, and blockchain-anchored credential verification. Ends in **9 literature gaps** and the functional/non-functional requirements (`FR-*`, `NFR-*`) derived from them. |
| **`Project_Objectives.pdf` / `.docx`** | **Objectives O1–O9**, one per literature gap, each traced to the requirement IDs it is implemented through. The `.docx` is a fully editable native Word document. |
| **`System_Design_Document.pdf` / `.docx`** | The architecture above: four (now five) detector services behind one orchestrator, one REST API, one data model — implements O1–O9. Includes an SVG architecture diagram, the data schema, and an NFR-to-design-decision mapping table. |
| **`Detailed_Design_Document.pdf` / `.docx`** | Class/component breakdown, algorithms, data structures, and interface specs for every service — down to real code excerpts for the assigned module — plus a message-level sequence diagram and system-wide error handling. |
| **`ForgeGuard_IEEE_Paper.docx` / `.pdf`** | An IEEE-format paper draft summarising the survey and approach, with the full 5-author byline. |

All five are generated from HTML source (`report.html`, `objectives.html`, `design.html`,
`detailed_design.html`, `paper.html`) via headless-Chrome PDF printing and a pandoc→python-docx
pipeline for the editable `.docx` versions — see [Building the documents](#building-the-documents).

## Repository layout

```
ForgeGuard-Project/
├── tamper_localisation/     # Service 1 — assigned module (see below)
├── signature_verification/  # Service 2
├── ocr_validation/          # Service 3
├── anomaly_detection/       # Service 4 (Phase 2)
├── fusion/                  # Service 5 — combines all of the above
├── ledger/                  # Phase 2 — hash-chain anchoring (pure logic)
├── api/                     # Orchestrator, SQLite persistence, auth/RBAC, REST routes
│   └── static/index.html    #   minimal browser test page
├── storage/heatmaps/        # Rendered heatmap overlays (generated at runtime, gitignored)
├── papers/, txt/            # The 52 literature-survey source papers (PDF) and text extracts
├── *.html, *_build.py       # Source templates + build scripts for the 5 project documents
├── *.pdf, *.docx            # The built project documents themselves
└── requirements.txt         # Full-system Python dependencies
```

Every one of the first six directories is real, working Python with its own self-check — there is
no directory in this list that is still just a design document. (An earlier version of this
repository also tracked five *generated* HTML build artifacts, which briefly made the repo's
language breakdown look HTML-heavy; those were removed from version control since they're fully
regenerable from the five real `.html` templates.)

## The five services, in detail

### 1. Tamper Detection and Localisation (`tamper_localisation/`)

The **assigned module** — the one the Detailed Design Document documents down to real code
excerpts. Detects and localises pixel-level image tampering (splicing, inpainting, copy-move).

- **`srm.py`** — 3 fixed, non-trainable Spatial Rich Model (SRM) high-pass filter kernels
  (horizontal residual, vertical residual, Laplacian-style), applied depthwise to every RGB
  channel. These expose noise-residual artefacts from editing that survive re-saving and are
  invisible to the eye — a classic forensic steganalysis technique.
- **`preprocess.py`** — deskew (a cheap row-variance angle search over ±10°, no OpenCV needed),
  resize/normalise to 256×256, and compute an Error Level Analysis (ELA) map (JPEG re-save at
  quality 90, pixel-wise diff) as one *supporting* signal alongside the SRM stream — not the sole
  signal, because the literature survey found ELA alone fails on clean, high-quality scans.
- **`model.py`** — `TamperLocaliser`: two independent encoders (an RGB+ELA stream, an SRM-residual
  stream, 32→64→128 channels each), fused with a 1×1 conv, decoded back up with 3 transpose-conv
  stages to a per-pixel tamper logit map. ~1.1M trainable parameters — small enough to run on CPU
  or one consumer GPU.
- **`dataset.py`** — a synthetic splice generator (a document-like page with a randomly pasted
  patch and a pixel-accurate ground-truth mask), with rotation/blur/noise/JPEG-recompression
  augmentation standing in for real print-scan degradation, until the FSD dataset (or real scans)
  is available.
- **`train.py` / `evaluate.py`** — a training loop (BCE + soft-Dice loss) and an evaluation script
  reporting precision/recall/F1/IoU/AUC on held-out data (never accuracy alone, per the
  literature's class-imbalance warning).
- **`infer.py`** — `TamperLocalisationService`, the module's only external surface:
  `predict(image) -> {mask, heatmap, score, regions}`. `score` is a 0–100 tamper-confidence value
  (`round(100 × (0.6 × peak-confidence + 0.4 × flagged-area-coverage))`); `regions` are the top 5
  suspicious connected components (via `scipy.ndimage.label`), each with a bounding box and
  confidence, for the visual explanation a reviewer sees.

### 2. Signature Verification (`signature_verification/`)

- **`detector.py`** — a heuristic signature-region detector: finds the largest, non-line-shaped
  ink blob on the page (connected-component analysis, filtered by area and aspect ratio to reject
  ruled lines). No object-detector training data exists yet, so this is a documented stand-in
  behind the exact same `detect()` contract a trained detector would use.
- **`cleaner.py`** — removes ruled lines (morphological opening with a wide horizontal/vertical
  structuring element) and small noise specks from the detected crop.
- **`encoder.py`** — `SignatureEncoder`: a small CNN (4 conv blocks, 16→32→64→128 channels) with
  an L2-normalised 64-dimensional embedding output, trained with **triplet loss** so that distance
  in embedding space reflects "same signer vs. different signer" rather than any one signer's
  identity — a new signer needs no retraining, only new reference embeddings.
- **`dataset.py`** — synthetic "signer styles": a seeded set of stroke control points rendered
  with small jitter for genuine variation, a different seed entirely for an impostor — a
  genuine-vs-impostor proxy standing in for CEDAR/BHSig260 until real signature data is available.
- **`train.py` / `evaluate.py`** — triplet-margin-loss training, and an **Equal Error Rate (EER)**
  evaluation (the metric the literature survey's signature papers actually report).
- **`service.py`** — `SignatureService.verify(page, references) -> {similarity, decision, bbox}`.
  Storage-agnostic by design: it takes a list of reference embeddings in, not a `signer_id` —
  looking a signer up in the `signatures` table is the orchestrator's job, keeping this module
  swappable without touching the data layer.

### 3. OCR / Field Validation (`ocr_validation/`)

- **`engine.py`** — shells out to the installed `tesseract` binary directly (no Python OCR
  dependency added — the ladder rule: use what's already installed).
- **`fields.py`** — per-document-type regex rules: date and ID-number patterns for
  identity/certificate/legal documents; currency-amount extraction (`total`/`net`/`tax`) for
  financial documents.
- **`arithmetic.py`** — the financial arithmetic gate: `|total − (net + tax)| ≤ tolerance`.
- **`service.py`** — `OCRService.check(page, doc_type) -> {fields, flags, arithmetic_ok, ocr_sub_score}`.
  An unrecognised `doc_type` skips field validation rather than silently scoring it as a pass or
  a fail — logged as a gap in rule coverage, not hidden.

### 4. Anomaly Detection (Phase 2) (`anomaly_detection/`)

Directly answers **Gap 8** of the literature survey ("supervised classifiers only learn the
forgery types they were trained on") and **Objective O8** ("add an anomaly detector later without
redesigning the pipeline") — Phase 2's "later" is now.

- **`model.py`** — `ConvAutoencoder`: a small convolutional encoder-decoder (16→32→64→128 channels
  down, mirrored back up) trained to reconstruct genuine documents.
- **`dataset.py`** — a genuine-only synthetic document generator, deliberately independent of
  `tamper_localisation`'s generator (no shared private helpers) so this module can be replaced
  without touching the tamper module.
- **`train.py`** — trains on **genuine pages only** — the autoencoder never sees a single forged
  example, so it carries no assumptions about what a forgery looks like. A forgery type nobody
  anticipated should still reconstruct poorly, simply because it doesn't look like what "genuine"
  looks like.
- **`evaluate.py`** — reports the AUC separating genuine reconstruction error from an unseen
  forgery type (reusing `tamper_localisation`'s splice generator purely as an evaluation stand-in,
  never for training) and calibrates a detection threshold as `mean + 2·std` of genuine error.
- **`service.py`** — `AnomalyDetectionService.predict(image) -> {score, reconstruction_error}`.
  `score` is scaled against the calibrated threshold with a tunable `SCALE` constant — see the
  `ponytail:` note in the file for why a narrow scale saturates almost any out-of-distribution
  genuine page to "100% anomalous" and how `SCALE=6` was chosen after observing that live.

### 5. Fusion & Scoring (`fusion/`)

The stage every other service's evidence flows into. **No end-to-end classifier** — a direct
response to Gap 5/6 of the survey (single-modality and opaque-decision systems miss forgeries and
can't be defended to a reviewer).

- Every sub-score is normalised to a common direction (0 = forged, 100 = genuine) before weighting.
  Signature similarity and the OCR pass-fraction are already genuine-direction; the tamper
  module's and the anomaly detector's scores are **forgery/anomaly-confidence** (higher = worse),
  so both are inverted (`100 − score`) — a real directional bug caught and fixed while building
  the fusion layer, now covered by a dedicated regression test
  (`test_tamper_direction_inverted`, `test_anomaly_direction_inverted`).
- `DEFAULT_WEIGHTS = {signature: 0.3, tamper: 0.3, ocr: 0.2, anomaly: 0.2}` — configuration, not
  code, so a deployment can recalibrate per document type without a redeploy.
- **A missing sub-score never lets the result reach "Genuine"**: its weight is redistributed
  across whatever evidence *is* available, and the label is capped at "Suspicious" (or lower).
  This applies uniformly to all four sources, including the Phase 2 anomaly score.
- The returned `reason` names the lowest-confidence available check and any missing evidence —
  e.g. *"lowest-confidence check: tamper (28/100); missing evidence: signature"* — so a verifier
  can see exactly why a document was flagged, not just that it was.

## The Ledger (Phase 2 — blockchain-style anchoring) (`ledger/`)

Answers **Gap 9** of the literature survey (blockchain anchoring proves integrity only for
documents issued through the system, and few detectors keep an auditable record of their own
decisions) and **Objective O9**.

This is a **local, permissioned hash chain** — not a public/distributed blockchain. There's no
network, no consensus, no smart contract. What it does give, which is the actual property Gap 9
asked for: **every verification's document hash becomes tamper-evident.** Each block stores
`{document_id, verification_id, document_hash, prev_hash, block_hash}`, where `block_hash` is the
SHA-256 of everything in the block including `prev_hash` — exactly the hash-linking mechanism a
real blockchain uses internally. `ledger/chain.py` holds the pure hash-chain math (no storage);
`api/db.py` persists blocks into a `ledger_blocks` table and anchors one new block per verification
from inside the orchestrator, right after the fused result is written.

**This was verified for real, not just unit-tested**: after anchoring two verifications, I edited
one block's stored `document_hash` directly in the SQLite file with a raw `UPDATE` statement —
bypassing the application entirely — and called `GET /admin/ledger/verify`. It correctly reported
`{"valid": false, "broken_at": 0}`, identifying the exact tampered block.

```python
# ponytail: a local hash chain, not a public ledger. Anchoring to a real chain
# (Ethereum/Hyperledger, papers [50], [51]) means swapping append()'s storage
# call for a transaction call; the block shape and verify_chain() contract
# stay the same.
```

## The Orchestrator and API (`api/`)

`api/orchestrator.py`'s `Orchestrator.verify()` is the only place that calls all five services:
pre-process once, run signature/tamper/OCR/anomaly, fuse, persist, anchor. If any one detector
raises an exception, the orchestrator catches it, logs it, and treats that evidence as *missing*
(not a failed request) — so a broken detector degrades the result instead of crashing the upload.

**Data layer** (`api/db.py`): SQLite (the already-installed stdlib option — Postgres is what the
System Design Document specifies for production; swapping the connection layer later changes
nothing about the schema or the query functions). Tables: `users`, `sessions`, `signatures`,
`documents`, `verifications`, `ledger_blocks`, `audit_log`.

**Auth & RBAC** (`api/auth.py`, NFR-9): every route except `/auth/*` and `/health` requires
`Authorization: Bearer <token>` from `/auth/login`; `/admin/*` routes additionally require the
`admin` role. Self-registration only ever creates a `verifier` account — `api/create_admin.py`
bootstraps an admin for testing. Passwords are SHA-256 hashed, tokens are opaque and
non-expiring — documented as a prototype-grade implementation (see the `ponytail:` note in
`api/auth.py`) that proves role separation end to end, not a hardened auth system.

**Routes:**

| Route | Auth | Description |
|---|---|---|
| `POST /auth/register` | — | Create a `verifier` account |
| `POST /auth/login` | — | Get a bearer token |
| `POST /signatures` | verifier | Register a reference signature for a signer |
| `POST /documents` | verifier | Upload a document; runs the full 5-service pipeline synchronously and returns the fused result |
| `GET /documents/{id}/verification` | verifier | Re-fetch a past result from SQLite |
| `GET /documents/{id}/heatmap` | verifier | The rendered tamper-heatmap overlay (PNG) |
| `GET /documents/{id}/anchor` | verifier | The ledger block anchoring this document's hash |
| `GET /admin/audit-log` | admin | The append-only audit trail |
| `GET /admin/ledger/verify` | admin | Re-derive every ledger block's hash and report whether the chain is unbroken |
| `GET /` | — | A minimal static test page (register/login, register a reference signature, upload a document, view the heatmap) |

A `POST /documents` response looks like:

```json
{
  "document_id": "...", "verification_id": "...",
  "score": 61, "label": "Suspicious",
  "reason": "lowest-confidence check: ocr (50/100); missing evidence: signature",
  "sub_scores": {"signature": null, "tamper": 72, "ocr": 50, "anomaly": 55},
  "tamper_regions": [{"bbox": [0, 0, 256, 256], "confidence": 0.53}],
  "signature_bbox": null,
  "ocr_fields": {"date": "01/02/2026"},
  "anomaly_reconstruction_error": 0.0019,
  "ledger_block": {"block_index": 3, "block_hash": "..."},
  "heatmap_url": "/documents/.../heatmap"
}
```

## Data design

| Table | Columns |
|---|---|
| `users` | `id`, `email` (unique), `password_hash`, `role` (`verifier`\|`admin`), `created_at` |
| `sessions` | `token` (PK), `user_id`, `created_at` |
| `signatures` | `id`, `signer_id`, `embedding` (JSON float array), `created_at` — 1–5 rows per signer |
| `documents` | `id`, `doc_type`, `sha256_hash`, `uploaded_at` |
| `verifications` | `id`, `document_id`, `signature_sub_score`, `tamper_sub_score`, `ocr_sub_score`, `anomaly_sub_score`, `final_score`, `label`, `reason_text`, `created_at` |
| `ledger_blocks` | `block_index` (PK), `document_id`, `verification_id`, `document_hash`, `prev_hash`, `block_hash`, `created_at` |
| `audit_log` | `id`, `action`, `verification_id`, `detail_json`, `created_at` — append-only, no `UPDATE`/`DELETE` path in application code |

## Setup and running the system

```bash
pip install -r requirements.txt      # torch, fastapi, uvicorn, scipy, scikit-learn, etc.
brew install tesseract               # OCR binary, shelled out to directly (no Python wrapper)

# self-check every service — no dataset needed for any of them
for m in tamper_localisation signature_verification ocr_validation fusion anomaly_detection ledger; do
  python3 -m $m.test_module
done

# run the API
uvicorn api.main:app --reload
# open http://127.0.0.1:8000 -- register an account, log in, register a reference
# signature, then upload a document (the page handles the bearer token for you)

# bootstrap an admin account (self-registration only ever creates "verifier")
python3 -m api.create_admin admin@example.com somepassword
```

`api/main.py` automatically loads `tamper_checkpoint.pt`, `signature_checkpoint.pt`, and
`anomaly_checkpoint.pt` from the repo root if present (all gitignored — train your own, or run
untrained for interface/contract testing only).

### Training each model

```bash
python3 -m tamper_localisation.train --epochs 15 --out tamper_checkpoint.pt
python3 -m tamper_localisation.evaluate --checkpoint tamper_checkpoint.pt --samples 128

python3 -m signature_verification.train --epochs 15 --out signature_checkpoint.pt
python3 -m signature_verification.evaluate --checkpoint signature_checkpoint.pt --samples 256

python3 -m anomaly_detection.train --epochs 15 --out anomaly_checkpoint.pt
python3 -m anomaly_detection.evaluate --checkpoint anomaly_checkpoint.pt --samples 150
```

### Building the documents

```bash
python3 build.py                      # -> Literature_Survey_Report.pdf
python3 objectives_build.py           # -> Project_Objectives.pdf
python3 objectives_docx_build.py      # -> Project_Objectives.docx (editable)
python3 design_build.py               # -> System_Design_Document.pdf
python3 design_docx_build.py          # -> System_Design_Document.docx (editable)
python3 detailed_design_build.py      # -> Detailed_Design_Document.pdf
python3 detailed_design_docx_build.py # -> Detailed_Design_Document.docx (editable)
python3 paper_build.py                # -> ForgeGuard_IEEE_Paper.pdf
python3 docx_build.py                 # -> ForgeGuard_IEEE_Paper.docx
```

Each `*_docx_build.py` must run after its matching `*_build.py` (it converts that script's
HTML output). All of these require Google Chrome installed at the default macOS path, and the
`.docx` builds additionally require `pandoc` and `python-docx`.

## Training results

A 15-epoch run on each of the three learned models, on their respective synthetic generators:

| Model | Metrics |
|---|---|
| Tamper localisation | precision 0.929, recall 0.966, **F1 0.947**, **IoU 0.900**, AUC 0.997 |
| Signature verification | **EER 1.6%**, accuracy 98.4% at the EER threshold (0.88) |
| Anomaly detection | **AUC 1.000** separating genuine reconstruction error from an unseen (spliced) forgery type |

These numbers describe how well each model learned its *synthetic* task, not real-document
accuracy — see [What's real vs. what's a documented stand-in](#whats-real-vs-whats-a-documented-stand-in).
What they do confirm, **verified live through the real API with the trained checkpoints loaded**,
not just the offline eval scripts:

- A genuine signature crop scores above an impostor's (55 vs. 14) through the full
  detect→clean→embed→compare path on a realistic page — not just on clean training-style renders.
- A tampered page scores below a genuine one on tamper evidence (21 vs. 45).
- A spliced page's anomaly reconstruction error is ~7× a genuine page's (0.0133 vs. 0.0019), and
  after recalibrating the score's dynamic range against that live observation, the genuine page
  reads as uncertain (55/100) while the tampered page reads as fully flagged (0/100) — not both
  saturated to the same value, which the first calibration attempt did.
- The ledger anchors every verification, and tampering a past block's stored hash directly in the
  database — bypassing the API — is detected by `GET /admin/ledger/verify` at the exact block.

## Testing

Every service ships a dependency-free self-check runnable with no dataset and no trained
checkpoint (`python3 -m <module>.test_module`), asserting real behaviour, not just "does it
import" — shape/contract checks, known-value checks (EER on a hand-computed example, pixel metrics
on a hand-computed 2×2 mask, hash-chain tampering detection), and directional checks (genuine >
impostor, tamper-direction inversion, anomaly-direction inversion). All six currently pass:
`tamper_localisation`, `signature_verification`, `ocr_validation`, `fusion`, `anomaly_detection`,
`ledger`.

Beyond the self-checks, the full system has been exercised live end to end multiple times through
a running `uvicorn` server with real HTTP requests — registration, login, role-based 401/403s,
signature registration, document upload with and without a registered signer, heatmap retrieval,
audit-log listing, ledger anchoring, and ledger-tampering detection — catching and fixing two real
bugs in the process (a SQLite thread-affinity crash under FastAPI's threadpool, and an
overly-strict signature-detector area threshold that rejected genuine thin pen strokes).

## What's real vs. what's a documented stand-in

Every simplification in this codebase is marked inline with a `# ponytail:` comment naming the
ceiling and what to upgrade to. The short version:

| Real, not a stand-in | Documented stand-in (training data) |
|---|---|
| Tesseract OCR (actual binary, actual text extraction) | `tamper_localisation`'s splice generator (stand-in for FSD, paper [29]) |
| SQLite persistence (actual writes/reads) | `signature_verification`'s signer-style generator (stand-in for CEDAR/BHSig260) |
| The hash-chain ledger and its tamper-detection property | `anomaly_detection`'s genuine-page generator |
| Auth/RBAC role separation | |
| Fusion's scoring/weighting/missing-evidence logic | |
| Every detector's fixed interface and the orchestrator's failure isolation | |

The **models trained on synthetic data** (tamper localisation, signature verification, anomaly
detection) have real, working training/evaluation pipelines producing real metrics — but those
metrics describe synthetic-task performance, not real-document accuracy, until each is retrained
on real labelled data. Swapping in real data means replacing one `dataset.py` per module; every
other file (model, service, training loop, evaluation script, orchestrator wiring) is unaffected,
by design.

## Status

**Both Phase 1 and Phase 2 are complete.**

- **Phase 1**: tamper localisation, signature verification, OCR/field validation, and fusion &
  scoring — all implemented, trained, tested, and wired through a working, authenticated REST API
  with SQLite persistence and an append-only audit log.
- **Phase 2**: an anomaly-detection worker (for forgery types outside the other models' training
  distribution) and a hash-chain ledger anchoring every verification's document hash — both
  implemented behind the same replaceable-detector interface as Phase 1, with no changes required
  to the orchestrator's existing detector-calling pattern beyond adding the new calls.

What remains explicitly out of scope, by original design choice, not as incomplete work: a public
blockchain network (the ledger is intentionally local/permissioned — see
[The Ledger](#the-ledger-phase-2--blockchain-style-anchoring-ledger)), and a polished production
web client (the static test page is functional, not a design deliverable). Real training datasets
for the three learned models remain the one dependency outside this repository's control — the
system is fully built and ready to retrain the moment that data is available.

## License

The papers under `papers/` and `txt/` are included for reference as part of the literature survey
and remain the copyright of their respective publishers (IEEE and others) — they are not covered
by any license on this repository's own content.
