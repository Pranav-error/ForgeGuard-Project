# Fill author names in paper.html and print the IEEE-style paper to PDF with headless Chrome.
import subprocess, pathlib
AUTHORS = ["Ruchikesha S", "Suhil Prasanth S", "Tara C", "Pavani V Reddy", "R Sai Pranav"]
AFF = "School of Computer Science &amp; Engineering<br>REVA University, Yelahanka, Bengaluru, India"
h = pathlib.Path("paper.html").read_text().replace(
    "{{AUTHORS}}", "".join(f'<div><div class="n">{a}</div>{AFF}</div>' for a in AUTHORS))
pathlib.Path("paper_out.html").write_text(h)
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu",
  "--no-pdf-header-footer", "--virtual-time-budget=8000", "--print-to-pdf=ForgeGuard_IEEE_Paper.pdf", "paper_out.html"], check=True, capture_output=True)
