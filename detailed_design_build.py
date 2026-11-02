# Fill placeholders in detailed_design.html and print the Detailed Design Document to PDF with headless Chrome.
import subprocess, pathlib
V = {
 "NAME": "R Sai Pranav", "USN": "R23EM069",
 "TITLE": "ForgeGuard: An AI-Based Document Forgery Detection and Verification System",
 "SHORT": "ForgeGuard", "TRACK": "PS 109", "GUIDE": "Mala B M",
 "DATE": "2 November 2026",
}
h = pathlib.Path("detailed_design.html").read_text()
for k, v in V.items(): h = h.replace("{{%s}}" % k, v)
assert "{{" not in h
pathlib.Path("detailed_design_out.html").write_text(h)
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu",
  "--no-pdf-header-footer", "--virtual-time-budget=8000", "--print-to-pdf=Detailed_Design_Document.pdf", "detailed_design_out.html"], check=True, capture_output=True)
