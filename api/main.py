"""ForgeGuard REST API -- FR-P1 (Detailed Design Document Section 8).

    uvicorn api.main:app --reload

Checkpoints are part of the app image and always load from ROOT. The SQLite
DB and heatmap files are *data*, not app code: they live under
FORGEGUARD_DATA_DIR (defaults to ROOT for local dev) so a hosting platform
can point it at a persistent volume -- e.g. Render's disk mounted at /data --
without surviving only as long as the container does.
"""
import os
import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from . import auth, db
from .orchestrator import Orchestrator
from .visualize import overlay_heatmap

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FORGEGUARD_DATA_DIR", str(ROOT)))
STORAGE = DATA_DIR / "storage" / "heatmaps"
STORAGE.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DATA_DIR / "forgeguard.db")

app = FastAPI(title="ForgeGuard")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

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


@app.get("/")
def index():
    return FileResponse(str(Path(__file__).parent / "static" / "index.html"))


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
    return {"token": token, "role": user["role"]}


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


@app.post("/documents")
async def upload_document(
    file: UploadFile,
    doc_type: str = Form(...),
    signer_id: str | None = Form(None),
    conn: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(current_user),
):
    page = Image.open(file.file).convert("RGB")
    result = orchestrator.verify(conn, page, doc_type, signer_id)

    heatmap = result.pop("_heatmap")
    heatmap_url = None
    if heatmap is not None:
        overlay = overlay_heatmap(page, heatmap)
        out_path = STORAGE / f"{result['document_id']}.png"
        overlay.save(out_path)
        heatmap_url = f"/documents/{result['document_id']}/heatmap"

    result["heatmap_url"] = heatmap_url
    return JSONResponse(result)


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
