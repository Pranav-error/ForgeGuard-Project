"""Request validation -- trust boundary checks on user-supplied uploads.

Before this, an invalid doc_type silently fell through (ocr_validation already handles an
unknown doc_type gracefully, by design), and a non-image upload crashed Image.open() into an
unhandled 500 instead of a clear 400. Neither is acceptable at a trust boundary (a user upload)
even though nothing downstream was actually unsafe.
"""
import io

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

ALLOWED_DOC_TYPES = {"identity", "certificate", "invoice", "legal"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB -- generous for a scanned page, not for abuse


def require_doc_type(doc_type: str) -> str:
    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(400, f"doc_type must be one of {sorted(ALLOWED_DOC_TYPES)}")
    return doc_type


async def load_image(upload: UploadFile) -> Image.Image:
    """Read, size-check, and decode an upload -- the one place this happens, so every route
    that accepts a file gets the same 400s instead of a 500 on bad input."""
    data = await upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"file too large (max {MAX_UPLOAD_BYTES // (1024*1024)}MB)")
    if not data:
        raise HTTPException(400, "empty file")
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(400, f"'{upload.filename}' is not a readable image")
