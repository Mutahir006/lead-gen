"""
Rule-based lead scoring. Plain Python — LangChain adds nothing here, this is
just if/else logic, so per the architecture rule we don't force it in.

An optional LLM-written one-line note is available separately (see
graph/pipeline.py, gated behind USE_LLM_SCORING) for when you actually want
natural-language judgment, not just arithmetic.
"""
from detection.website_detector import STATUS_NOT_FOUND, STATUS_FOUND
from detection.ai_tool_detector import STATUS_NOT_DETECTED, STATUS_DETECTED

HIGH_VALUE_CATEGORIES = {"care home", "clinic", "dental", "salon", "hotel", "restaurant"}


def score_lead(lead: dict) -> dict:
    score = 0
    reasons = []

    if lead.get("website_status") == STATUS_NOT_FOUND:
        score += 4
        reasons.append("No website — strong web-dev prospect")
    elif lead.get("website_status") == STATUS_FOUND:
        score += 1
        reasons.append("Has a website already — lower web-dev priority")

    if lead.get("ai_tool_status") == STATUS_NOT_DETECTED:
        score += 3
        reasons.append("No AI chatbot/voice tool detected on site")
    elif lead.get("ai_tool_status") == STATUS_DETECTED:
        score -= 3
        reasons.append(f"Already using {lead.get('ai_tool_vendor')} — deprioritize")

    category = (lead.get("category") or "").lower()
    if any(hv in category for hv in HIGH_VALUE_CATEGORIES):
        score += 2
        reasons.append("High-value category for your agency")

    if score >= 7:
        status = "HOT"
    elif score >= 4:
        status = "WARM"
    else:
        status = "COLD"

    lead["lead_score"] = score
    lead["lead_status"] = status
    lead["score_reasons"] = reasons
    return lead
