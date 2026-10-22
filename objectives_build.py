# Fill placeholders in objectives.html and print the Project Objectives doc to PDF with headless Chrome.
import subprocess, pathlib
V = {
 "NAME": "[Your Name]", "USN": "[Your USN]",
 "TITLE": "ForgeGuard: An AI-Based Document Forgery Detection and Verification System",
 "SHORT": "ForgeGuard", "TRACK": "[Track]", "CENTRE": "[Centre]", "GUIDE": "[Faculty Guide]",
 "DATE": "22 October 2026",
}
h = pathlib.Path("objectives.html").read_text()
for k, v in V.items(): h = h.replace("{{%s}}" % k, v)
assert "{{" not in h
pathlib.Path("objectives_out.html").write_text(h)
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu",
  "--no-pdf-header-footer", "--virtual-time-budget=8000", "--print-to-pdf=Project_Objectives.pdf", "objectives_out.html"], check=True, capture_output=True)
