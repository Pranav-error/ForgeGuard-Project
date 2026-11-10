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
- [The Web Frontend (`web/`)](#the-web-frontend-web)
- [Competitive research behind this round](#competitive-research-behind-this-round)
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
├── web/                     # React + Vite + TypeScript + Tailwind frontend (see below)
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

**Input validation at trust boundaries** (`api/validation.py`): every route that accepts an
upload (`/signatures`, `/documents`, `/documents/batch`) routes through `load_image()`, which
caps upload size (10MB), rejects empty bodies, and decodes the file through PIL — a non-image
upload now returns a clean `400` instead of an unhandled `500` crashing out of `Image.open()`.
`require_doc_type()` allowlists `doc_type` the same way, so an unrecognized value is rejected
up front instead of silently falling through downstream. Batch upload validates `doc_type` once
for the whole request, then isolates per-file failures into that file's result row instead of
failing the entire batch.

**Routes:**

| Route | Auth | Description |
|---|---|---|
| `POST /auth/register` | — | Create a `verifier` account |
| `POST /auth/login` | — | Get a bearer token |
| `POST /signatures` | verifier | Register a reference signature for a signer |
| `POST /documents` | verifier | Upload a document; runs the full 5-service pipeline synchronously and returns the fused result |
| `POST /documents/batch` | verifier | Same pipeline, one `doc_type` applied to any number of files in one request — competing products (Onfido, Jumio, AU10TIX) all offer bulk processing; this is the minimal real version |
| `GET /documents/{id}/verification` | verifier | Re-fetch a past result from SQLite |
| `GET /documents/{id}/heatmap` | verifier | The rendered tamper-heatmap overlay (PNG) |
| `GET /documents/{id}/report.pdf` | verifier | A downloadable PDF verification report (`api/report.py`, reportlab) — declared as FR-U3 from the first design draft, not actually built until now |
| `GET /documents/{id}/anchor` | verifier | The ledger block anchoring this document's hash |
| `GET /admin/audit-log` | admin | The append-only audit trail |
| `GET /admin/ledger/verify` | admin | Re-derive every ledger block's hash and report whether the chain is unbroken |
| `GET /verifications` | verifier | The signed-in user's own past verifications (History page) |
| `GET /analytics/summary` | verifier | Label breakdown, score averages, 14-day activity series (Analytics page) — not bare `/analytics`, see below |
| `GET /{anything-else}` | — | Falls through to the React app's `index.html` (client-side routing) — see [The Web Frontend](#the-web-frontend-web) |

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

## The Web Frontend (`web/`)

A real React app — Vite + React + TypeScript + Tailwind CSS v4, React Router for client-side
routing, no CDN dependency at runtime (everything is compiled at build time). It replaced an
earlier single-page vanilla-HTML version after that version both looked unconvincing (one long
scrolling form, no real navigation) and had a real bug: it loaded Tailwind from
`cdn.tailwindcss.com`, which never loaded in the browser-automation environment used to test it,
silently breaking the entire layout. A real build step has no such runtime dependency to fail.

**Pages**, each a real route (`/`, `/login`, `/dashboard`, `/verify`, `/history`, `/analytics`, `/admin`):

| Route | Purpose |
|---|---|
| `/` | Public landing page — what ForgeGuard is, the four services, a "Get started" CTA. |
| `/login` | Sign in / create account (tab-switched), stores the session in `sessionStorage`. |
| `/dashboard` | Signed-in home — links to Verify, History and Analytics (and Admin, if the role is `admin`). |
| `/verify` | Register a reference signature, upload a document, see the full result (score, label, reason, four sub-score bars, heatmap overlay, raw JSON, a PDF report download) — and a third card for batch-verifying several documents at once, results in a table. |
| `/history` | Every document *this user* has verified (needs `documents.uploaded_by`, added for this), each row expandable with a report-download button. |
| `/analytics` | Total verifications, average score, label-breakdown bars, average sub-scores, and a 14-day activity chart — hand-rolled SVG/CSS, no charting library pulled in for four small visualisations. |
| `/admin` | Audit log table + a button that runs the ledger integrity check live. Guarded client-side; the API enforces the real guard (`auth.require_admin`). |

**Auth across pages:** the bearer token, role and email live in `sessionStorage` (not just a JS
variable — that would lose the session on every navigation in a real multi-page app), read into a
React context (`src/lib/auth.tsx`) that every page consumes via `useAuth()`. `ProtectedRoute` and
`AdminRoute` (`src/components/ProtectedRoute.tsx`) redirect to `/login` (or show a "for
administrators only" message) before rendering anything that needs a session.

**Heatmap images are fetched, not `<img src>`'d directly** — `GET /documents/{id}/heatmap`
requires the same bearer token every other route does, and `<img>` can't attach custom headers.
Caught this live (broken-image icon in the browser); fixed by fetching the PNG with the header and
handing the `<img>` a `URL.createObjectURL()` blob instead (`api.fetchHeatmap` in `src/lib/api.ts`).

**The heatmap visualisation itself was also fixed.** The first version blended the continuous
heatmap over the whole page; on a genuinely out-of-distribution input (a random photo, tried live
while reviewing this) the model's output saturates almost everywhere and the overlay became a
solid red wash — reads as "broken," not "here's the suspicious region." `api/visualize.py` now
tints only the thresholded mask and draws numbered boxes around the actual top regions, so it
stays legible even on nonsense input.

**Build/serve:** `npm run build` in `web/` produces `web/dist/`; `api/main.py` serves it from the
same FastAPI process (`/assets/*` for the hashed JS/CSS bundles, everything else falls through to
`index.html` so React Router's own client-side routes work on a hard refresh — a plain
`StaticFiles(html=True)` mount only does that fallback for `/` itself, not for `/dashboard` etc.,
which 404'd until this was added). One Docker image, one Render service, same as before — see
[Deploying to Render](#deploying-to-render); the Dockerfile now multi-stage builds the frontend
with `node:20-slim` before the Python stage copies in `web/dist/`.

For local development: run the backend (`uvicorn api.main:app --reload`) and, separately,
`npm run dev` in `web/` — its dev server proxies `/auth`, `/signatures`, `/documents`,
`/verifications`, `/admin/audit-log`, `/admin/ledger/*` and `/health` back to the backend (see
`web/vite.config.ts`). That proxy config deliberately does **not** use a bare `/admin` prefix —
it would also swallow requests to the SPA's own `/admin` *page* route, which shares the prefix
with the `/admin/*` API routes (caught live: a hard refresh on `/admin` returned the backend's
raw 404 JSON instead of the page). The same collision bit `/analytics` directly: the API route
was originally bare `GET /analytics`, *identical* to the page's own path, so a hard refresh there
always hit the API handler first and showed `{"detail":"missing bearer token"}` instead of the
page — caught live after reconnecting the browser mid-session. Fixed by moving the API route to
`/analytics/summary`, matching the `/admin/audit-log` pattern: the bare path is always the page.

## Competitive research behind this round

Every major competitor in this space (Onfido, Jumio, Veriff, AU10TIX) converges on the same
feature set: document authenticity + biometric/liveness checks + configurable risk scoring +
downloadable compliance reports + analytics dashboards + batch processing. ForgeGuard already had
strong document authenticity (four fused detectors) and configurable risk scoring (fusion
weights); the honestly-missing pieces were a downloadable report (declared as FR-U3 since the
first design draft, never built), analytics, and batch processing — all three closed this round.
Biometric/liveness checks (selfie-to-ID face matching) remain explicitly out of scope: building
one honestly needs real face data this project doesn't have, the same reasoning that kept the
other learned models on synthetic stand-ins rather than a weaker, unconvincing version of a
pretrained-face-model wrapper.

## Data design

| Table | Columns |
|---|---|
| `users` | `id`, `email` (unique), `password_hash`, `role` (`verifier`\|`admin`), `created_at` |
| `sessions` | `token` (PK), `user_id`, `created_at` |
| `signatures` | `id`, `signer_id`, `embedding` (JSON float array), `created_at` — 1–5 rows per signer |
| `documents` | `id`, `uploaded_by`, `doc_type`, `sha256_hash`, `uploaded_at` |
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

# run the backend
uvicorn api.main:app --reload

# in a second terminal: run the frontend dev server (proxies API calls to the backend above)
cd web && npm install && npm run dev
# open http://localhost:5173 -- register an account, sign in, register a reference
# signature, then upload a document

# bootstrap an admin account (self-registration only ever creates "verifier")
python3 -m api.create_admin admin@example.com somepassword
```

To run it the way it's actually deployed — one process, no separate dev server — build the
frontend and let the backend serve it:

```bash
cd web && npm install && npm run build && cd ..
uvicorn api.main:app --reload
# open http://127.0.0.1:8000
```

`api/main.py` automatically loads `tamper_checkpoint.pt`, `signature_checkpoint.pt`, and
`anomaly_checkpoint.pt` from the repo root if present. The three checkpoints trained for this
project (see [Training results](#training-results)) are committed to the repo — small enough
(~3.4MB total) that there's no reason to make a hosted deployment retrain on boot. Retrain your
own with the commands below any time; the new files overwrite the committed ones.

### Deploying to Render

The app is Dockerised (`Dockerfile`) because it needs the `tesseract` binary installed alongside
the Python/torch stack, and `render.yaml` describes it as a Render **Blueprint**: an always-on web
service with a 1GB persistent disk mounted at `/data`, so the SQLite DB, uploaded-document hashes,
heatmaps, and the ledger survive restarts and redeploys — not just the container's own filesystem.

This needs a paid plan: Render's **free tier has no persistent-disk support and spins the service
down after 15 minutes of inactivity**, which fails both "always-on" and "persistent." The
Blueprint requests the **Starter** plan (~$7/month) plus the disk's own small monthly cost — both
billed to whoever connects the repo, since that requires a Render account and payment method.

1. Push this repo to GitHub (already done) and sign in to Render with that GitHub account.
2. **New** → **Blueprint**, select this repo. Render reads `render.yaml` and proposes the
   `forgeguard` web service with its disk already configured — review and **Apply**.
3. First boot builds the Docker image (a few minutes, mostly the torch install) and starts
   `uvicorn` bound to Render's `$PORT`. Check `https://<your-service>.onrender.com/health`.
4. Create an admin account on the deployed instance — Render's dashboard has a **Shell** tab for
   the running service:
   ```bash
   python3 -m api.create_admin admin@example.com somepassword
   ```
   (`FORGEGUARD_DATA_DIR=/data` is already set from `render.yaml`, so this writes to the
   persistent disk, not the container's throwaway filesystem.)
5. Open the service URL — the same React app as local dev, now talking to the hosted API.

Local development is unaffected: `FORGEGUARD_DATA_DIR` defaults to the repo root when unset, which
is what running `uvicorn api.main:app --reload` on your own machine still does.

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
- **Frontend**: a real React + Vite + TypeScript + Tailwind single-page app (`web/`) with seven
  routes — including Analytics and batch verification — persistent sessions, and role-gated pages,
  served by the same backend in one Docker image. See [The Web Frontend](#the-web-frontend-web).
- **Closed the competitive gaps found by researching Onfido/Jumio/Veriff/AU10TIX**: a downloadable
  PDF verification report (`api/report.py`, declared as FR-U3 since the first design draft, never
  built until now), an Analytics dashboard, and batch document verification.

What remains explicitly out of scope, by original design choice, not as incomplete work: a public
blockchain network (the ledger is intentionally local/permissioned — see
[The Ledger](#the-ledger-phase-2--blockchain-style-anchoring-ledger)). Real training datasets for
the three learned models remain the one dependency outside this repository's control — the system
is fully built and ready to retrain the moment that data is available.

## License

The papers under `papers/` and `txt/` are included for reference as part of the literature survey
and remain the copyright of their respective publishers (IEEE and others) — they are not covered
by any license on this repository's own content.
