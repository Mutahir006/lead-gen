"""
Website presence check.
This is mostly free info — Google Places already tells us if a business has
listed a website. We just interpret it carefully instead of trusting it blindly.
"""

STATUS_FOUND = "FOUND"
STATUS_NOT_FOUND = "NOT_FOUND"
STATUS_UNCERTAIN = "UNCERTAIN"


def detect_website_status(place: dict) -> str:
    """
    place: normalized place dict from google_places.normalize_place()

    Logic:
    - If business_status isn't OPERATIONAL, we can't trust the data -> UNCERTAIN
    - If a websiteUri is present -> FOUND
    - Otherwise -> NOT_FOUND (Google Business Profiles are usually well-maintained
      for this field, but treat it as a reasonably-confident signal, not gospel)
    """
    business_status = place.get("business_status", "UNKNOWN")

    if business_status not in ("OPERATIONAL",):
        return STATUS_UNCERTAIN

    website = (place.get("website") or "").strip()
    if website:
        return STATUS_FOUND

    return STATUS_NOT_FOUND
