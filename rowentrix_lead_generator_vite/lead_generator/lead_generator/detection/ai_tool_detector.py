"""
Detects whether a business's site already runs an AI chatbot or voice-agent
widget, using the vendor signatures in signatures.py.

Vercel note: Playwright (headless browser rendering) is deliberately NOT used
here. It's too heavy for a serverless bundle and too slow to fit inside a
10-60 second function timeout across multiple sites. This version does a
static HTML fetch only, run CONCURRENTLY across all leads via a thread pool
so 10-20 sites finish in the time one would take sequentially. This means it
will miss chat widgets that only inject via JavaScript after page load — an
accepted tradeoff for the hosted version. Everything's tagged UNCERTAIN
rather than silently wrong.

Important limitation either way: this can only see what's on the WEBSITE.
A business using an AI phone receptionist with no web widget shows as
NOT_DETECTED/NOT_APPLICABLE here even if they do use one — that's not a
confirmed absence.
"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from detection.signatures import ALL_SIGNATURES

STATUS_DETECTED = "DETECTED"
STATUS_NOT_DETECTED = "NOT_DETECTED"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
STATUS_UNCERTAIN = "UNCERTAIN"


def _scan_html(html: str):
    lower = html.lower()
    for vendor, patterns in ALL_SIGNATURES.items():
        for pattern in patterns:
            if pattern.lower() in lower:
                return vendor
    return None


def detect_ai_tools(website: str) -> dict:
    """Single-site check. Used directly by the CLI / for one-off lookups."""
    if not website:
        return {"status": STATUS_NOT_APPLICABLE, "vendor": None}

    try:
        resp = requests.get(website, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        vendor = _scan_html(resp.text)
        if vendor:
            return {"status": STATUS_DETECTED, "vendor": vendor}
        return {"status": STATUS_NOT_DETECTED, "vendor": None}
    except Exception:
        return {"status": STATUS_UNCERTAIN, "vendor": None}


def detect_ai_tools_bulk(leads: list, max_workers: int = 10) -> list:
    """
    Runs detect_ai_tools() across all leads concurrently and writes the
    result straight onto each lead dict. This is what the hosted pipeline
    calls, so a 10-lead batch takes roughly as long as ONE slow site,
    not the sum of all of them.
    """
    def _worker(lead):
        result = detect_ai_tools(lead.get("website"))
        lead["ai_tool_status"] = result["status"]
        lead["ai_tool_vendor"] = result["vendor"]
        return lead

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_worker, lead) for lead in leads]
        for f in as_completed(futures):
            f.result()  # raises here if a worker had an unhandled error

    return leads
