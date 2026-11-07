"""OCR extraction -- FR-D3.

Shells out to the installed `tesseract` binary rather than adding a Python
OCR dependency (ladder rule: use what's already installed).

# ponytail: single engine. The System Design Document calls for a 3-engine
# consensus on financial documents (FORENSIQ, paper [39]); add Tesseract +
# EasyOCR + PaddleOCR majority-vote once those are available, same
# OCREngine.extract_text() contract.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

TESSERACT = shutil.which("tesseract")


def extract_text(image: Image.Image) -> str:
    if TESSERACT is None:
        raise RuntimeError("tesseract binary not found on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        img_path = Path(tmp) / "page.png"
        image.convert("RGB").save(img_path)
        result = subprocess.run(
            [TESSERACT, str(img_path), "stdout"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout
