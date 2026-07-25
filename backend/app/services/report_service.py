"""
Report Service — PDF generation using ReportLab.

Pipeline: Upload → Vision → OCR → Comparison → AI → [PDF]

Generates a 3-page professional inspection report:
  Page 1: Header, Inspection Summary, Fraud Score, Verdict
  Page 2: Vision Analysis, OCR Fields, Comparison Results
  Page 3: AI Reasoning, Recommendations, Sign-off
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.core.config import settings
from app.models.ai_analysis import AIAnalysisResult
from app.models.comparison import ComparisonResult
from app.models.ocr import OCRResult
from app.models.report import ReportResult
from app.models.vision import VisionResult
from app.utils.results_store import (
    STAGE_AI, STAGE_COMPARISON, STAGE_OCR, STAGE_VISION, STAGE_REPORT,
    load_result, save_result,
)

logger = logging.getLogger(__name__)

# Colours
DELL_BLUE = colors.HexColor("#0076CE")
DARK_BG = colors.HexColor("#1E293B")
VERDICT_COLORS = {
    "AUTHENTIC": colors.HexColor("#10B981"),
    "SUSPICIOUS": colors.HexColor("#F59E0B"),
    "COUNTERFEIT": colors.HexColor("#EF4444"),
}


def generate_report(inspection_id: str) -> ReportResult:
    """Generate a PDF inspection report and return its path."""
    vision = load_result(inspection_id, STAGE_VISION, VisionResult)
    ocr = load_result(inspection_id, STAGE_OCR, OCRResult)
    comparison = load_result(inspection_id, STAGE_COMPARISON, ComparisonResult)
    ai = load_result(inspection_id, STAGE_AI, AIAnalysisResult)

    report_dir = settings.UPLOAD_DIR / inspection_id / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = report_dir / "inspection_report.pdf"

    _build_pdf(str(pdf_path), inspection_id, vision, ocr, comparison, ai)

    relative = str(pdf_path.relative_to(settings.UPLOAD_DIR.parent))
    result = ReportResult(
        inspection_id=inspection_id,
        report_path=relative,
        generated_at=datetime.utcnow(),
        page_count=3,
    )
    save_result(inspection_id, STAGE_REPORT, result)
    logger.info("PDF report generated: %s", relative)
    return result


def _build_pdf(
    path: str,
    inspection_id: str,
    vision: VisionResult,
    ocr: OCRResult,
    comparison: ComparisonResult,
    ai: AIAnalysisResult,
) -> None:
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # ── Title styles ──────────────────────────────────────────────────────────
    title_style = ParagraphStyle("Title", parent=styles["Title"], textColor=DELL_BLUE, fontSize=22, spaceAfter=6)
    heading2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=DELL_BLUE, fontSize=13, spaceBefore=12, spaceAfter=4)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, spaceAfter=4, leading=14)
    verdict_color = VERDICT_COLORS.get(ai.verdict, colors.gray)

    # ── Page 1: Header & Summary ──────────────────────────────────────────────
    story.append(Paragraph("Dell PartVision AI", title_style))
    story.append(Paragraph("Hardware Authenticity Inspection Report", styles["Heading2"]))
    story.append(HRFlowable(width="100%", thickness=2, color=DELL_BLUE))
    story.append(Spacer(1, 0.4*cm))

    meta = [
        ["Inspection ID", inspection_id],
        ["Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Verdict", ai.verdict],
        ["Fraud Score", f"{ai.fraud_score} / 100"],
        ["AI Confidence", ai.confidence_level],
        ["AI Model", ai.ai_model_used],
    ]
    meta_table = Table(meta, colWidths=[5*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
        ("TEXTCOLOR", (0, 0), (0, -1), DELL_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 2), (1, 2), verdict_color),
        ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Dell Fields ───────────────────────────────────────────────────────────
    story.append(Paragraph("Extracted Dell Label Fields", heading2))
    f = ocr.combined_dell_fields
    fields_data = [
        ["Field", "Extracted Value", "Status"],
        ["Service Tag", f.service_tag or "[NOT FOUND]", "[OK]" if f.service_tag else "[FAIL]"],
        ["Express Service Code", f.express_service_code or "[NOT FOUND]", "[OK]" if f.express_service_code else "[FAIL]"],
        ["Part Number", f.part_number or "[NOT FOUND]", "[OK]" if f.part_number else "[FAIL]"],
        ["Model Name", f.model_name or "[NOT FOUND]", "[OK]" if f.model_name else "[FAIL]"],
        ["Country of Origin", f.country_of_origin or "N/A", "[INFO]"],
        ["Manufacture Date", f.manufacture_date or "N/A", "[INFO]"],
        ["Regulatory", ", ".join(f.regulatory_info) or "None found", "[INFO]"],
    ]
    ft = Table(fields_data, colWidths=[5*cm, 9*cm, 3*cm])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DELL_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ft)
    story.append(Spacer(1, 0.4*cm))

    # ── Page 2: Vision + Comparison ───────────────────────────────────────────
    story.append(Paragraph("Computer Vision Analysis", heading2))
    story.append(Paragraph(
        f"Front image: blur_score={vision.front.quality.blur_score}, "
        f"is_blurry={vision.front.quality.is_blurry}, "
        f"brightness={vision.front.quality.mean_brightness:.1f}, "
        f"edge_density={vision.front.edge_density}, "
        f"label_regions={len(vision.front.label_regions)}.", body
    ))
    story.append(Paragraph(
        f"Back image: blur_score={vision.back.quality.blur_score}, "
        f"is_blurry={vision.back.quality.is_blurry}.", body
    ))
    story.append(Paragraph(
        f"Overall quality ok: {vision.overall_quality_ok}. "
        f"Flags: {', '.join(vision.vision_flags) or 'None'}.", body
    ))

    story.append(Paragraph("Comparison Engine Results", heading2))
    story.append(Paragraph(comparison.comparison_summary, body))
    for chk in comparison.field_checks:
        icon = "[OK]" if chk.is_present and chk.is_valid_format else "[WARN]" if chk.is_present else "[FAIL]"
        story.append(Paragraph(
            f"{icon} <b>{chk.field_name}</b>: {chk.extracted_value or 'N/A'} — risk +{chk.risk_contribution}",
            body
        ))
    story.append(Paragraph(f"<b>Total comparison risk: {comparison.total_risk_score}/100</b>", body))

    # ── Page 3: AI Reasoning ──────────────────────────────────────────────────
    story.append(Paragraph("AI Reasoning", heading2))
    story.append(Paragraph(f"<b>Visual Analysis:</b> {ai.visual_analysis}", body))
    story.append(Paragraph(f"<b>Text Analysis:</b> {ai.text_analysis}", body))
    story.append(Paragraph(f"<b>Discrepancy Analysis:</b> {ai.discrepancy_analysis}", body))
    story.append(Paragraph(f"<b>Final Reasoning:</b> {ai.final_reasoning}", body))

    story.append(Paragraph("Recommendations", heading2))
    for i, rec in enumerate(ai.recommendations, 1):
        story.append(Paragraph(f"{i}. {rec}", body))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1")))
    story.append(Paragraph(
        f"Generated by Dell PartVision AI v1.0 | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.gray, alignment=1)
    ))

    doc.build(story)
