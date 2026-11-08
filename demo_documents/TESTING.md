# Testing ForgeGuard

Six demo documents in this folder exercise every code path in the pipeline. Open the app
(locally at `http://127.0.0.1:8000`, or the hosted instance) and work through them in order.

**Hosted instance:** https://forgeguard-2wmt.onrender.com — free tier, so the **first
request after a few minutes idle takes ~30-60s to wake up**; it's fine after that. Data
resets on redeploy (no persistent disk on the free tier).

## 1. Sign in

Create an account (any email/password) under "Account", then switch to "Sign in" and log in.
Steps 2 and 3 unlock once you're signed in.

## 2. Register a reference signature

- **Signer ID:** `demo_signer`
- **Signature crop image:** `reference_signature.png`

Click **Register signature**.

## 3. Upload each document

All six use `demo_signer` as the Signer ID (leave blank to see signature evidence reported as
"missing" instead).

| File | Document type | Expect |
|---|---|---|
| `genuine_identity.png` | Identity card | Signature sub-score noticeably higher than the impostor/tampered cases below (genuine vs. impostor ordering holds; the model is trained on synthetic data, so don't expect a near-100 absolute score — see the README's "What's real vs. what's a documented stand-in"). OCR 100 (both fields read cleanly). |
| `impostor_signature.png` | Identity card | Same page, but signed by a *different* synthetic signer than the registered reference — signature sub-score visibly lower than `genuine_identity`'s. |
| `tampered_identity.png` | Identity card | Same page with a spliced patch pasted on. Tamper sub-score visibly lower than `genuine_identity`'s, and the heatmap overlay shows a reddish region where the splice landed. |
| `invoice_correct.png` | Invoice | OCR sub-score 100 — Net ($200.00) + Tax ($20.00) = Total ($220.00), arithmetic gate passes. |
| `invoice_mismatched.png` | Invoice | OCR sub-score 50 — Total is $500.00, which doesn't equal Net+Tax, so the arithmetic gate fails and halves the OCR sub-score. Overall label drops to Forged. |

For each upload, check:
- The four sub-score cards (signature/tamper/ocr/anomaly) and their colors
- The **reason** text naming the lowest-confidence check
- The **heatmap overlay** (tamper + impostor + genuine docs all produce one; invoices don't
  need to be examined visually in the same way, but the tamper model still runs on them)
- Expand **Raw response** to see the full JSON, including `ledger_block` (every upload anchors
  a new block — the index increments each time)

## 4. Try the missing-evidence path

Upload any document **without** a Signer ID. `sub_scores.signature` comes back `null`, the
reason text says `missing evidence: signature`, and the label is capped below "Genuine" even if
everything else looks good — the fusion stage never reaches "Genuine" on partial evidence.

## 5. Admin-only routes (optional)

These aren't in the web UI (no admin screens were built — just the two routes). To try them,
you need an admin account:

```bash
# locally
python3 -m api.create_admin you@example.com yourpassword

# on the hosted Render instance, via the dashboard's Shell tab (needs your Render SSH key
# added first for `render ssh` / direct ssh to work — the Shell tab in the browser doesn't)
```

Then, with that account's token:

```bash
curl -s <base-url>/admin/audit-log -H "Authorization: Bearer <admin-token>"
curl -s <base-url>/admin/ledger/verify -H "Authorization: Bearer <admin-token>"
```

`ledger/verify` re-derives every block's hash and reports whether the chain is unbroken —
try editing a block's `document_hash` directly in `forgeguard.db` with a raw `UPDATE`
statement and re-running it to see it catch the tamper at the exact block (this is exactly
how it was verified while building the ledger — see the README).

## Regenerating these documents

`demo_documents/` is generated, not hand-made — see the script embedded in the project history,
or recreate similarly with `signature_verification.dataset.render_style_sample` (for
signatures) and plain `PIL.ImageDraw` **with a real TrueType font** (e.g.
`/System/Library/Fonts/Supplemental/Arial.ttf` on macOS — PIL's default bitmap font is too
low-resolution for Tesseract to read reliably; this was learned the hard way building this
exact kit: "Total" OCR'd as "Totat" at the default font, silently breaking the invoice
demo's arithmetic-gate test until the font was fixed).
