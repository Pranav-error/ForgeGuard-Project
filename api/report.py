"""PDF verification report -- FR-U3 ("download a verification report as a PDF"), declared in
the System Design Document's API table since the first draft but never actually built until now.
Every competing product in this space (Onfido, Jumio, Veriff, AU10TIX) ships a downloadable
per-verification report; this closes that specific, previously-unbuilt gap.

Pure-Python (reportlab), not the headless-Chrome pipeline the academic documents use -- that
needs a full Chrome install, which the production Docker image deliberately doesn't carry
(NFR-2: this service should stay light). A verification report is generated per-request from a
handful of known fields, so a direct canvas/platypus layout is the simpler tool for the job.
"""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LABEL_COLORS = {
    "Genuine": colors.HexColor("#047857"),
    "Suspicious": colors.HexColor("#b45309"),
    "Forged": colors.HexColor("#b91c1c"),
    "Failed": colors.HexColor("#475569"),
}


def build_report_pdf(document: dict, verification: dict, heatmap_path: str | None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=4)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#64748b"))
    label_color = LABEL_COLORS.get(verification["label"], LABEL_COLORS["Failed"])
    # leading set explicitly: the parent's leading (22pt) was sized for its 18pt fontSize, not
    # this style's 28pt -- left inherited, the line box was shorter than the text itself and
    # visually collided with the next paragraph (confirmed live: "Score: n/100" and the label
    # rendered on top of each other instead of stacked).
    score_style = ParagraphStyle("Score", parent=styles["Title"], fontSize=28, leading=34, textColor=label_color, spaceAfter=4)
    reason_style = ParagraphStyle("Reason", parent=styles["Normal"], fontSize=10, leading=14)

    flow = [
        Paragraph("ForgeGuard Verification Report", title_style),
        Paragraph(
            f"Document {document['id']} &middot; verified {verification['created_at']}",
            meta_style,
        ),
        Spacer(1, 16),
        Paragraph(f"{verification['label']}", score_style),
        Paragraph(f"Score: {verification['final_score'] if verification['final_score'] is not None else '—'} / 100", styles["Normal"]),
        Spacer(1, 10),
        Paragraph(verification["reason_text"], reason_style),
        Spacer(1, 16),
    ]

    sub_rows = [["Check", "Sub-score"]]
    for key, label in [("signature_sub_score", "Signature"), ("tamper_sub_score", "Tamper"),
                        ("ocr_sub_score", "OCR / Field"), ("anomaly_sub_score", "Anomaly")]:
        val = verification.get(key)
        sub_rows.append([label, str(val) if val is not None else "N/A"])
    sub_table = Table(sub_rows, colWidths=[3 * inch, 2 * inch])
    sub_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#475569")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow += [sub_table, Spacer(1, 18)]

    meta_rows = [
        ["Document type", document["doc_type"]],
        ["Document SHA-256", document["sha256_hash"]],
        ["Uploaded at", document["uploaded_at"]],
        ["Verification ID", verification["id"]],
    ]
    meta_table = Table(meta_rows, colWidths=[1.6 * inch, 4.4 * inch])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#94a3b8")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    flow += [meta_table, Spacer(1, 18)]

    if heatmap_path:
        flow.append(Paragraph("Tamper heatmap overlay", ParagraphStyle("H3", parent=styles["Heading3"], fontSize=10)))
        flow.append(Spacer(1, 6))
        # bordered: most of a genuine page is unflagged (plain white), which otherwise makes
        # the embedded image look cut off or broken against the report's own white background
        # -- confirmed live on a near-blank test page, where only ~0.5% of pixels were non-white.
        framed = Table([[Image(heatmap_path, width=3.1 * inch, height=3.1 * inch)]], colWidths=[3.2 * inch])
        framed.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        flow.append(framed)
        flow.append(Spacer(1, 16))

    flow.append(Paragraph(
        "Generated by ForgeGuard. This report reflects the state of the system's hash-chain "
        "ledger and detector models at the time of verification; see /admin/ledger/verify for "
        "integrity of the underlying record.",
        meta_style,
    ))

    doc.build(flow)
    return buf.getvalue()
