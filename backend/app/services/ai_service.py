"""
AI Reasoning Service — LangGraph + GPT-4.1.

Pipeline: Upload → Vision → OCR → Comparison → [AI] → PDF

LangGraph workflow:
  load_context → analyze_visual → analyze_text → analyze_discrepancies → synthesize → score

Fallback: if OPENAI_API_KEY is not set, uses rule-based scoring.
"""

import logging
from typing import Any, Dict, List, TypedDict

from app.core.config import settings
from app.models.ai_analysis import AIAnalysisResult
from app.models.comparison import ComparisonResult
from app.models.vision import VisionResult
from app.models.ocr import OCRResult
from app.utils.results_store import (
    STAGE_AI, STAGE_COMPARISON, STAGE_OCR, STAGE_VISION,
    load_result, save_result,
)

logger = logging.getLogger(__name__)


class InspectionState(TypedDict):
    inspection_id: str
    vision: Dict[str, Any]
    ocr: Dict[str, Any]
    comparison: Dict[str, Any]
    visual_analysis: str
    text_analysis: str
    discrepancy_analysis: str
    final_reasoning: str
    fraud_score: int
    verdict: str
    confidence_level: str
    recommendations: List[str]


def run_ai_analysis(inspection_id: str) -> AIAnalysisResult:
    """
    Run the full LangGraph AI reasoning pipeline.
    Falls back to rule-based scoring if no OpenAI key is configured.
    """
    vision = load_result(inspection_id, STAGE_VISION, VisionResult)
    ocr = load_result(inspection_id, STAGE_OCR, OCRResult)
    comparison = load_result(inspection_id, STAGE_COMPARISON, ComparisonResult)

    if settings.OPENAI_API_KEY:
        result = _run_langgraph(inspection_id, vision, ocr, comparison)
    else:
        logger.warning("OPENAI_API_KEY not set — using rule-based fallback for inspection %s", inspection_id)
        result = _rule_based_fallback(inspection_id, vision, ocr, comparison)

    save_result(inspection_id, STAGE_AI, result)
    return result


def _run_langgraph(
    inspection_id: str,
    vision: VisionResult,
    ocr: OCRResult,
    comparison: ComparisonResult,
) -> AIAnalysisResult:
    """Build and run a LangGraph reasoning workflow."""
    from langgraph.graph import StateGraph, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = ChatOpenAI(model="gpt-4.1", temperature=0.2, api_key=settings.OPENAI_API_KEY)

    # ── Pre-build context strings ─────────────────────────────────────────────
    vision_ctx = (
        f"Front image: blur_score={vision.front.quality.blur_score}, "
        f"is_blurry={vision.front.quality.is_blurry}, "
        f"edge_density={vision.front.edge_density}, "
        f"label_regions={len(vision.front.label_regions)}, "
        f"quality_flags={vision.front.quality_flags}. "
        f"Back image: blur_score={vision.back.quality.blur_score}, "
        f"is_blurry={vision.back.quality.is_blurry}. "
        f"Overall quality ok: {vision.overall_quality_ok}."
    )
    ocr_ctx = (
        f"Extracted fields — "
        f"Service Tag: {ocr.combined_dell_fields.service_tag}, "
        f"ESC: {ocr.combined_dell_fields.express_service_code}, "
        f"Part Number: {ocr.combined_dell_fields.part_number}, "
        f"Model: {ocr.combined_dell_fields.model_name}, "
        f"Regulatory: {ocr.combined_dell_fields.regulatory_info}, "
        f"Front OCR confidence: {ocr.front.avg_confidence:.2%}, "
        f"Back OCR confidence: {ocr.back.avg_confidence:.2%}."
    )
    golden_used = comparison.golden_reference_used or "None"
    metrics = comparison.similarity_metrics or {}
    cmp_ctx = (
        f"Golden Reference Profile Used: {golden_used}. "
        f"Similarity Metrics against Golden: OCR Similarity={metrics.get('ocr_similarity', 100)}/100, "
        f"Vision Match={metrics.get('vision_match', 100)}/100, "
        f"Anomaly Score={metrics.get('anomaly_score', 0)}/100. "
        f"Comparison risk score: {comparison.total_risk_score}/100. "
        f"Missing fields: {comparison.missing_critical_fields}. "
        f"Format violations: {comparison.format_violations}. "
        f"{comparison.comparison_summary}"
    )

    SYSTEM = (
        "You are an expert Dell hardware authenticity inspector with 15 years experience. "
        "Analyse the provided inspection data and give precise, concise technical assessments. "
        "You are comparing the uploaded part against a known Golden Reference Profile. "
        "Be factual, explicitly reference differences from the Golden Profile, and be decisive."
    )

    def call_llm(prompt: str) -> str:
        resp = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])
        return str(resp.content).strip()

    # ── Node functions ────────────────────────────────────────────────────────
    def analyze_visual(state: InspectionState) -> InspectionState:
        analysis = call_llm(
            f"Analyse these computer vision signals from a Dell hardware part inspection.\n"
            f"Vision data: {vision_ctx}\n"
            f"In 2-3 sentences, assess image quality and what the visual signals suggest about authenticity."
        )
        return {**state, "visual_analysis": analysis}

    def analyze_text(state: InspectionState) -> InspectionState:
        analysis = call_llm(
            f"Analyse these OCR-extracted text fields from a Dell hardware label.\n"
            f"OCR data: {ocr_ctx}\n"
            f"In 2-3 sentences, assess whether the text fields look authentic or suspicious."
        )
        return {**state, "text_analysis": analysis}

    def analyze_discrepancies(state: InspectionState) -> InspectionState:
        analysis = call_llm(
            f"Analyse these comparison engine results for a Dell hardware part against the Golden Reference.\n"
            f"Comparison data: {cmp_ctx}\n"
            f"Visual context: {state['visual_analysis']}\n"
            f"Text context: {state['text_analysis']}\n"
            f"In 2-3 sentences, summarise how much the uploaded part deviates from the Golden Reference and what the anomalies indicate."
        )
        return {**state, "discrepancy_analysis": analysis}

    def synthesize(state: InspectionState) -> InspectionState:
        reasoning = call_llm(
            f"Based on all inspection signals, provide a final authenticity verdict for this Dell hardware part.\n"
            f"Visual: {state['visual_analysis']}\n"
            f"Text: {state['text_analysis']}\n"
            f"Discrepancies: {state['discrepancy_analysis']}\n"
            f"Comparison risk: {comparison.total_risk_score}/100\n\n"
            f"Respond ONLY in this exact JSON format (no markdown):\n"
            f'{{"verdict": "AUTHENTIC|SUSPICIOUS|COUNTERFEIT", '
            f'"confidence": "HIGH|MEDIUM|LOW", '
            f'"fraud_score": <int 0-100>, '
            f'"reasoning": "<2-4 sentence final reasoning>", '
            f'"recommendations": ["<action1>", "<action2>", "<action3>"]}}'
        )
        import json, re
        try:
            # Strip markdown code fences if present
            clean = re.sub(r'```json?\s*|```', '', reasoning).strip()
            parsed = json.loads(clean)
            return {
                **state,
                "final_reasoning": parsed.get("reasoning", reasoning),
                "fraud_score": max(0, min(100, int(parsed.get("fraud_score", comparison.total_risk_score)))),
                "verdict": parsed.get("verdict", "SUSPICIOUS"),
                "confidence_level": parsed.get("confidence", "MEDIUM"),
                "recommendations": parsed.get("recommendations", []),
            }
        except Exception:
            score = comparison.total_risk_score
            verdict = "AUTHENTIC" if score < 30 else "SUSPICIOUS" if score < 60 else "COUNTERFEIT"
            return {
                **state,
                "final_reasoning": reasoning,
                "fraud_score": score,
                "verdict": verdict,
                "confidence_level": "LOW",
                "recommendations": ["Manual inspection recommended."],
            }

    # ── Build graph ───────────────────────────────────────────────────────────
    graph = StateGraph(InspectionState)
    graph.add_node("analyze_visual", analyze_visual)
    graph.add_node("analyze_text", analyze_text)
    graph.add_node("analyze_discrepancies", analyze_discrepancies)
    graph.add_node("synthesize", synthesize)
    graph.set_entry_point("analyze_visual")
    graph.add_edge("analyze_visual", "analyze_text")
    graph.add_edge("analyze_text", "analyze_discrepancies")
    graph.add_edge("analyze_discrepancies", "synthesize")
    graph.add_edge("synthesize", END)
    compiled = graph.compile()

    initial_state: InspectionState = {
        "inspection_id": inspection_id,
        "vision": vision.model_dump(),
        "ocr": ocr.model_dump(),
        "comparison": comparison.model_dump(),
        "visual_analysis": "",
        "text_analysis": "",
        "discrepancy_analysis": "",
        "final_reasoning": "",
        "fraud_score": 0,
        "verdict": "SUSPICIOUS",
        "confidence_level": "MEDIUM",
        "recommendations": [],
    }

    final = compiled.invoke(initial_state)
    logger.info("LangGraph complete for %s — verdict=%s score=%d", inspection_id, final['verdict'], final['fraud_score'])

    return AIAnalysisResult(
        inspection_id=inspection_id,
        visual_analysis=final["visual_analysis"],
        text_analysis=final["text_analysis"],
        discrepancy_analysis=final["discrepancy_analysis"],
        final_reasoning=final["final_reasoning"],
        fraud_score=final["fraud_score"],
        verdict=final["verdict"],
        confidence_level=final["confidence_level"],
        recommendations=final["recommendations"],
        ai_model_used="gpt-4.1",
    )


def _rule_based_fallback(
    inspection_id: str,
    vision: VisionResult,
    ocr: OCRResult,
    comparison: ComparisonResult,
) -> AIAnalysisResult:
    """Rule-based analysis when no LLM key is available."""
    score = comparison.total_risk_score
    if not vision.overall_quality_ok:
        score = min(100, score + 10)

    verdict = "AUTHENTIC" if score < 30 else "SUSPICIOUS" if score < 60 else "COUNTERFEIT"
    confidence = "HIGH" if score < 20 or score > 70 else "MEDIUM"

    visual_analysis = (
        f"Image quality {'acceptable' if vision.overall_quality_ok else 'poor — retake recommended'}. "
        f"Front blur score: {vision.front.quality.blur_score:.1f}, "
        f"edge density: {vision.front.edge_density:.4f}. "
        f"{len(vision.front.label_regions)} label region(s) detected."
    )
    text_analysis = (
        f"OCR extracted: Service Tag={'present' if ocr.combined_dell_fields.service_tag else 'MISSING'}, "
        f"Part Number={'present' if ocr.combined_dell_fields.part_number else 'MISSING'}, "
        f"Model={'present' if ocr.combined_dell_fields.model_name else 'MISSING'}. "
        f"Average OCR confidence: {(ocr.front.avg_confidence + ocr.back.avg_confidence)/2:.2%}."
    )
    discrepancy_analysis = comparison.comparison_summary
    final_reasoning = (
        f"Rule-based analysis (no AI key configured). "
        f"Comparison risk score: {comparison.total_risk_score}/100. "
        f"Missing fields: {comparison.missing_critical_fields or 'none'}. "
        f"Format violations: {comparison.format_violations or 'none'}."
    )
    recommendations = []
    if comparison.missing_critical_fields:
        recommendations.append(f"Investigate missing fields: {', '.join(comparison.missing_critical_fields)}.")
    if not vision.overall_quality_ok:
        recommendations.append("Retake images with better lighting and focus.")
    if verdict == "COUNTERFEIT":
        recommendations.append("Quarantine part immediately and escalate to QA Manager.")
    elif verdict == "SUSPICIOUS":
        recommendations.append("Request physical verification by senior technician.")
    else:
        recommendations.append("Part cleared for use. Archive inspection record.")

    return AIAnalysisResult(
        inspection_id=inspection_id,
        visual_analysis=visual_analysis,
        text_analysis=text_analysis,
        discrepancy_analysis=discrepancy_analysis,
        final_reasoning=final_reasoning,
        fraud_score=score,
        verdict=verdict,
        confidence_level=confidence,
        recommendations=recommendations,
        ai_model_used="rule-based-fallback",
    )
