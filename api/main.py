"""ForgeGuard REST API -- FR-P1 (Detailed Design Document Section 8).

    uvicorn api.main:app --reload

Checkpoints are part of the app image and always load from ROOT. The SQLite
DB and heatmap files are *data*, not app code: they live under
FORGEGUARD_DATA_DIR (defaults to ROOT for local dev) so a hosting platform
can point it at a persistent volume -- e.g. Render's disk mounted at /data --
without surviving only as long as the container does.

The frontend is the React app in web/ (Vite + React Router). Its production
build (web/dist/, produced by the Dockerfile) is served from "/" with
html=True so client-side routes (e.g. /dashboard on a hard refresh) fall
back to index.html -- mounted *after* every API route below so it never
shadows them. For local development, run the backend here and `npm run dev`
in web/ separately (its Vite dev server proxies API calls back to this app).
"""
import os
import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

from . import auth, db
from .orchestrator import Orchestrator
from .report import build_report_pdf
from .visualize import overlay_heatmap

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FORGEGUARD_DATA_DIR", str(ROOT)))
STORAGE = DATA_DIR / "storage" / "heatmaps"
STORAGE.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DATA_DIR / "forgeguard.db")
STATIC_DIR = ROOT / "web" / "dist"  # the built React app (web/) -- see Dockerfile

app = FastAPI(title="ForgeGuard")

orchestrator: Orchestrator | None = None


@app.on_event("startup")
def startup():
    global orchestrator
    db.connect(DB_PATH).close()  # ensure schema exists
    tamper_ckpt = ROOT / "tamper_checkpoint.pt"
    signature_ckpt = ROOT / "signature_checkpoint.pt"
    anomaly_ckpt = ROOT / "anomaly_checkpoint.pt"
    orchestrator = Orchestrator(
        tamper_checkpoint=str(tamper_ckpt) if tamper_ckpt.exists() else None,
        signature_checkpoint=str(signature_ckpt) if signature_ckpt.exists() else None,
        anomaly_checkpoint=str(anomaly_ckpt) if anomaly_ckpt.exists() else None,
    )


def get_db():
    conn = db.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def current_user(
    conn: sqlite3.Connection = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> dict:
    return auth.get_current_user(conn, authorization)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register")
def register(email: str = Form(...), password: str = Form(...), conn: sqlite3.Connection = Depends(get_db)):
    if db.get_user_by_email(conn, email):
        raise HTTPException(409, "email already registered")
    user_id = db.add_user(conn, email, auth.hash_password(password), role="verifier")
    return {"id": user_id, "email": email, "role": "verifier"}


@app.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...), conn: sqlite3.Connection = Depends(get_db)):
    user = db.get_user_by_email(conn, email)
    if user is None or not auth.verify_password(password, user["password_hash"]):
        raise HTTPException(401, "invalid credentials")
    token = auth.new_token()
    db.add_session(conn, user["id"], token)
    return {"token": token, "role": user["role"], "email": user["email"]}


@app.post("/signatures")
async def register_signature(
    signer_id: str = Form(...),
    image: UploadFile = None,
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(current_user),
):
    if image is None:
        raise HTTPException(400, "image file required")
    crop = Image.open(image.file)
    embedding = orchestrator.signature.embed(crop)
    row_id = db.add_signature(conn, signer_id, embedding)
    return {"id": row_id, "signer_id": signer_id}


def _verify_one(conn: sqlite3.Connection, user: dict, page: Image.Image, doc_type: str, signer_id: str | None) -> dict:
    """Shared by /documents and /documents/batch -- same pipeline call, same heatmap handling."""
    result = orchestrator.verify(conn, page, doc_type, signer_id, uploaded_by=user["id"])

    heatmap = result.pop("_heatmap")
    heatmap_url = None
    if heatmap is not None:
        overlay = overlay_heatmap(page, heatmap, result.get("tamper_regions") or [])
        out_path = STORAGE / f"{result['document_id']}.png"
        overlay.save(out_path)
        heatmap_url = f"/documents/{result['document_id']}/heatmap"

    result["heatmap_url"] = heatmap_url
    return result


@app.post("/documents")
async def upload_document(
    file: UploadFile,
    doc_type: str = Form(...),
    signer_id: str | None = Form(None),
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(current_user),
):
    page = Image.open(file.file).convert("RGB")
    return JSONResponse(_verify_one(conn, user, page, doc_type, signer_id))


@app.post("/documents/batch")
async def upload_batch(
    files: list[UploadFile],
    doc_type: str = Form(...),
    signer_id: str | None = Form(None),
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(current_user),
):
    """Batch verification -- the same single-document pipeline run once per file, in one
    request. Competing products (Onfido, Jumio, AU10TIX) all offer bulk/batch processing;
    this is the minimal real version of that, not a separate queueing system."""
    results = []
    for f in files:
        try:
            page = Image.open(f.file).convert("RGB")
            r = _verify_one(conn, user, page, doc_type, signer_id)
            results.append({"filename": f.filename, **r})
        except Exception as e:
            results.append({"filename": f.filename, "error": str(e)})
    return JSONResponse(results)


@app.get("/documents/{document_id}/report.pdf")
def get_report(document_id: str, conn: sqlite3.Connection = Depends(get_db), user: dict = Depends(current_user)):
    """FR-U3: a downloadable verification report -- every competing product in this space
    ships one; this was declared in the design docs from the start but never built until now."""
    document = db.get_document(conn, document_id)
    verification = db.get_verification(conn, document_id)
    if document is None or verification is None:
        raise HTTPException(404, "not found")
    heatmap_path = STORAGE / f"{document_id}.png"
    pdf_bytes = build_report_pdf(document, verification, str(heatmap_path) if heatmap_path.exists() else None)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="forgeguard-report-{document_id[:8]}.pdf"'},
    )


@app.get("/analytics/summary")
def analytics(conn: sqlite3.Connection = Depends(get_db), user: dict = Depends(current_user)):
    # not bare "/analytics": that's also the SPA's own page route, so a hard refresh or direct
    # navigation there would hit this handler first (no auth header on a plain navigation) and
    # show raw JSON instead of the page -- caught live, same bug class as the earlier /admin fix.
    return db.analytics_for_user(conn, user["id"])


@app.get("/verifications")
def list_verifications(conn: sqlite3.Connection = Depends(get_db), user: dict = Depends(current_user)):
    return db.list_verifications_for_user(conn, user["id"])


@app.get("/documents/{document_id}/verification")
def get_verification(document_id: str, conn: sqlite3.Connection = Depends(get_db), user: dict = Depends(current_user)):
    row = db.get_verification(conn, document_id)
    if row is None:
        raise HTTPException(404, "not found")
    heatmap_path = STORAGE / f"{document_id}.png"
    row["heatmap_url"] = f"/documents/{document_id}/heatmap" if heatmap_path.exists() else None
    return row


@app.get("/documents/{document_id}/heatmap")
def get_heatmap(document_id: str, user: dict = Depends(current_user)):
    path = STORAGE / f"{document_id}.png"
    if not path.exists():
        raise HTTPException(404, "not found")
    return FileResponse(str(path))


@app.get("/admin/audit-log")
def audit_log(conn: sqlite3.Connection = Depends(get_db), user: dict = Depends(current_user)):
    auth.require_admin(user)
    return db.list_audit_log(conn)


@app.get("/documents/{document_id}/anchor")
def get_anchor(document_id: str, conn: sqlite3.Connection = Depends(get_db), user: dict = Depends(current_user)):
    """Phase 2: the ledger block that anchors this document's hash (Gap 9 / O9)."""
    block = db.get_block_for_document(conn, document_id)
    if block is None:
        raise HTTPException(404, "not found")
    return block


@app.get("/admin/ledger/verify")
def verify_ledger(conn: sqlite3.Connection = Depends(get_db), user: dict = Depends(current_user)):
    """Phase 2: re-derive every block's hash and check the chain is unbroken."""
    auth.require_admin(user)
    return db.verify_chain(conn)


# Registered last so neither ever shadows an API route above:
# - /assets/* are the hashed JS/CSS bundles Vite's build produces.
# - every other path (/, /dashboard, /verify on a hard refresh, ...) gets the SPA shell;
#   StaticFiles(html=True) alone only does this for "/" itself, not for client-side routes
#   that don't correspond to a real file (confirmed live: GET /dashboard 404'd without this).
app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    return FileResponse(str(STATIC_DIR / "index.html"))
