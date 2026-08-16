"""
Business data source: OpenStreetMap (Nominatim geocoding + Overpass API).
No API key, no billing account, no signup — genuinely free, forever.

Trade-off vs Google Places: OSM data is community-mapped, so coverage and
accuracy vary by area. Well-mapped UK cities are generally solid; smaller
towns can be patchy or missing recently-opened businesses. Treat this as
"good enough to find real leads," not "as complete as Google."

Two-step process:
1. Nominatim geocodes the city name to an OSM administrative area ID.
2. Overpass queries that area for businesses matching a category tag.

Both are public, free services with fair-use rate limits (Nominatim: max
1 request/second; Overpass: shared public server, be reasonable with volume).
If you outgrow the public Overpass server, you can self-host one or use a
paid Overpass mirror — not needed for normal lead-gen volumes.
"""
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Required by Nominatim's usage policy — identify your app, don't spoof a browser.
# IMPORTANT: put YOUR real email below. Nominatim's abuse filter specifically
# blocks the generic "you@example.com" placeholder that shows up in every
# tutorial — that's why the original version got a 403.
HEADERS = {"User-Agent": "RowentrixLeadGenerator/1.0 (contact: mutahirshahzad001@gmail.com)"}

# Maps free-text categories (what you type on the --category flag / form field)
# to OpenStreetMap tags. This is the part you'll extend over time — OSM tagging
# is categorical, not free text, so anything not in this map can't be searched.
# Add more as you need them: https://wiki.openstreetmap.org/wiki/Map_features
CATEGORY_TAGS = {
    "restaurant": ("amenity", "restaurant"),
    "cafe": ("amenity", "cafe"),
    "coffee": ("amenity", "cafe"),
    "hotel": ("tourism", "hotel"),
    "care home": ("amenity", "nursing_home"),
    "nursing home": ("amenity", "nursing_home"),
    "clinic": ("amenity", "clinic"),
    "dentist": ("amenity", "dentist"),
    "dental": ("amenity", "dentist"),
    "salon": ("shop", "hairdresser"),
    "hairdresser": ("shop", "hairdresser"),
    "plumber": ("craft", "plumber"),
    "electrician": ("craft", "electrician"),
    "gym": ("leisure", "fitness_centre"),
    "pub": ("amenity", "pub"),
    "bar": ("amenity", "bar"),
    "pharmacy": ("amenity", "pharmacy"),
    "veterinary": ("amenity", "veterinary"),
    "vet": ("amenity", "veterinary"),
    "bakery": ("shop", "bakery"),
    "supermarket": ("shop", "supermarket"),
    "estate agent": ("office", "estate_agent"),
    "accountant": ("office", "accountant"),
    "solicitor": ("office", "lawyer"),
    "lawyer": ("office", "lawyer"),
}


def _resolve_category(category: str):
    cat_lower = category.lower().strip()
    for phrase, tag in CATEGORY_TAGS.items():
        if phrase in cat_lower:
            return tag
    raise ValueError(
        f"'{category}' isn't mapped to an OpenStreetMap tag yet. "
        f"Add it to CATEGORY_TAGS in sources/osm_places.py. "
        f"Currently known categories: {', '.join(CATEGORY_TAGS.keys())}"
    )


def _geocode_area(city: str, country: str) -> int:
    """Returns an Overpass area ID for the given city's administrative boundary."""
    params = {"q": f"{city}, {country}", "format": "json", "limit": 1}
    resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
    if resp.status_code == 403:
        raise RuntimeError(
            "Nominatim returned 403 Forbidden. This almost always means the "
            "User-Agent header in osm_places.py still has a placeholder email — "
            "edit HEADERS at the top of this file and put your real contact info in."
        )
    resp.raise_for_status()
    results = resp.json()

    if not results:
        raise ValueError(f"Could not geocode '{city}, {country}' via Nominatim")

    result = results[0]
    if result.get("osm_type") != "relation":
        raise ValueError(
            f"'{city}' didn't resolve to an administrative area boundary "
            f"(got {result.get('osm_type')}) — try a more specific/exact city name"
        )

    # Overpass area IDs for relations are the OSM relation ID + 3,600,000,000
    return 3600000000 + int(result["osm_id"])


def search_businesses(city: str, category: str, country: str = "UK", max_results: int = 20):
    """
    Returns a list of raw Overpass elements (not yet our lead schema).
    """
    tag_key, tag_value = _resolve_category(category)
    area_id = _geocode_area(city, country)

    query = f"""
    [out:json][timeout:25];
    area({area_id})->.searchArea;
    (
      node["{tag_key}"="{tag_value}"](area.searchArea);
      way["{tag_key}"="{tag_value}"](area.searchArea);
    );
    out center tags;
    """

    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])
    return elements[:max_results]


def normalize_place(element: dict, category: str, city: str) -> dict:
    """Convert an Overpass element into the fields our pipeline works with."""
    tags = element.get("tags", {})

    website = tags.get("website") or tags.get("contact:website") or ""
    phone = tags.get("phone") or tags.get("contact:phone") or ""
    postcode = tags.get("addr:postcode", "")
    housenumber = tags.get("addr:housenumber", "")
    street = tags.get("addr:street", "")
    address = " ".join(p for p in [housenumber, street] if p) or tags.get("addr:full", "")

    return {
        "place_id": f"osm_{element.get('type')}_{element.get('id')}",
        "business_name": tags.get("name", "Unknown"),
        "category": category,
        "address": address,
        "city": city,
        "postcode": postcode,
        "website": website,
        "phone": phone,
        # OSM doesn't reliably track open/closed status the way Google does —
        # we assume operational unless you later add disused:* tag handling.
        "business_status": "OPERATIONAL",
        "source": "OpenStreetMap",
    }
