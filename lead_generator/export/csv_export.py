"""
CSV export. Two versions:
- export_to_csv(): writes a file to disk. Fine for local CLI use.
- leads_to_csv_string(): builds the CSV in memory and returns it as text.
  This is what the hosted API uses — Vercel's filesystem is read-only/ephemeral,
  so "write a file and return its path" doesn't work there.
"""
import csv
import io
from datetime import datetime

from db import fetch_leads

FIELDNAMES = [
    "business_name", "category", "address", "city", "postcode",
    "website", "phone", "website_status", "ai_tool_status", "ai_tool_vendor",
    "lead_score", "lead_status", "source",
]


def leads_to_csv_string(min_score: int = 0) -> str:
    leads = fetch_leads(min_score=min_score)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDNAMES, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(leads)
    return buffer.getvalue()


def export_to_csv(min_score: int = 0, filename: str = None) -> str:
    """Local/CLI use only — writes an actual file to disk."""
    if filename is None:
        filename = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    csv_string = leads_to_csv_string(min_score=min_score)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        f.write(csv_string)

    return filename
