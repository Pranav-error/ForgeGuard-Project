# Fill placeholders in report.html and print to PDF with headless Chrome.
import subprocess, pathlib
V = {
 "NAME": "R Sai Pranav", "USN": "R23EM069",
 "TITLE": "ForgeGuard: An AI-Based Document Forgery Detection and Verification System",
 "SHORT": "ForgeGuard", "TRACK": "PS 109", "GUIDE": "Mala B M",
 "DATE": "12 October 2026",
 "MODULE_INTRO": "The requirements that apply directly to the assigned module, Document Tamper Detection and Localisation, are listed below. The module takes a pre-processed document image, computes noise-residual (SRM) and ELA maps, runs a dual-stream localisation network (an SRM stream and a semantic RGB stream with an encoder-decoder), and returns a pixel-level heatmap and a tamper sub-score to the fusion stage. It runs server-side behind the common API and is shared by the web interface and any future client.",
 "MODULE_ITEMS": "\n".join(f"<li>{x}</li>" for x in [
  "FR-D1. The module deskews, resizes and normalises the uploaded page and computes the SRM noise-residual and ELA maps used as inputs.",
  "FR-D2. The module is the core of this requirement: it localises tampered regions and outputs a pixel-level mask and heatmap over the document.",
  "FR-D5. The module returns a tamper sub-score from 0 to 100, which the fusion stage combines with the signature and OCR sub-scores.",
  "FR-D6. The module supplies the heatmap and the largest suspicious regions, with their coordinates, for the explanation shown to the verifier.",
  "FR-A2. Documents flagged as Suspicious, together with the administrator's final decision, are stored as labelled feedback for retraining the module.",
  "NFR-1 and NFR-2. Localisation of a single page takes no more than a few seconds and runs on a single consumer GPU or on CPU.",
  "NFR-5. The module is evaluated on FSD and on a synthetic inpainting set with pixel-level precision, recall, F1 and IoU, not with accuracy alone.",
  "NFR-7. The localiser sits behind a fixed interface (image in, mask and score out), so it can be replaced by a newer model without changes elsewhere.",
  "NFR-10. Training uses augmentation for rotation, scaling, noise, blur, recompression and print-scan, so that the module stays robust under real capture conditions.",
 ]),
}
h = pathlib.Path("report.html").read_text()
for k, v in V.items(): h = h.replace("{{%s}}" % k, v)
assert "{{" not in h
pathlib.Path("out.html").write_text(h)
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu",
  "--no-pdf-header-footer", "--virtual-time-budget=8000", "--print-to-pdf=Literature_Survey_Report.pdf", "out.html"], check=True, capture_output=True)
