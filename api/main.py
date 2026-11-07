"""ForgeGuard REST API -- FR-P1 (Detailed Design Document Section 8).

    uvicorn api.main:app --reload
"""
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from . import db
from .orchestrator import Orchestrator
from .visualize import overlay_heatmap

ROOT = Path(__file__).resolve().parent.parent
STORAGE = ROOT / "storage" / "heatmaps"
STORAGE.mkdir(parents=True, exist_ok=True)
DB_PATH = str(ROOT / "forgeguard.db")

app = FastAPI(title="ForgeGuard")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

orchestrator: Orchestrator | None = None


@app.on_event("startup")
def startup():
    global orchestrator
    db.connect(DB_PATH).close()  # ensure schema exists
    orchestrator = Orchestrator()


@app.get("/")
def index():
    return FileResponse(str(Path(__file__).parent / "static" / "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/signatures")
async def register_signature(signer_id: str = Form(...), image: UploadFile = None):
    if image is None:
        raise HTTPException(400, "image file required")
    crop = Image.open(image.file)
    embedding = orchestrator.signature.embed(crop)
    with db.session(DB_PATH) as conn:
        row_id = db.add_signature(conn, signer_id, embedding)
    return {"id": row_id, "signer_id": signer_id}


@app.post("/documents")
async def upload_document(
    file: UploadFile,
    doc_type: str = Form(...),
    signer_id: str | None = Form(None),
):
    page = Image.open(file.file).convert("RGB")

    with db.session(DB_PATH) as conn:
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
def get_verification(document_id: str):
    with db.session(DB_PATH) as conn:
        row = db.get_verification(conn, document_id)
    if row is None:
        raise HTTPException(404, "not found")
    heatmap_path = STORAGE / f"{document_id}.png"
    row["heatmap_url"] = f"/documents/{document_id}/heatmap" if heatmap_path.exists() else None
    return row


@app.get("/documents/{document_id}/heatmap")
def get_heatmap(document_id: str):
    path = STORAGE / f"{document_id}.png"
    if not path.exists():
        raise HTTPException(404, "not found")
    return FileResponse(str(path))
