"""Airbnb scraper — Python port of @openbnb/mcp-server-airbnb."""

import json
from base64 import b64decode
from typing import Any, Optional
from urllib.parse import quote, urlencode

import requests

USER_AGENT = (
    "ModelContextProtocol/1.0 "
    "(Autonomous; +https://github.com/modelcontextprotocol/servers)"
)
BASE_URL = "https://www.airbnb.com"
TIMEOUT = 30


def _fetch(url: str) -> str:
    resp = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cache-Control": "no-cache",
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.text


def _extract_json_data(html: str) -> dict:
    """Extract the embedded JSON data from Airbnb's #data-deferred-state-0 script tag."""
    marker = 'id="data-deferred-state-0"'
    idx = html.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find data-deferred-state-0 script element")

    # Find the script content between > and </script>
    start = html.find(">", idx) + 1
    end = html.find("</script>", start)
    if start <= 0 or end == -1:
        raise RuntimeError("Could not parse script element content")

    script_text = html[start:end].strip()
    if not script_text:
        raise RuntimeError("Data script element is empty")

    return json.loads(script_text)


def _clean_object(obj: Any) -> Any:
    """Remove None values and empty containers recursively."""
    if isinstance(obj, dict):
        return {
            k: _clean_object(v)
            for k, v in obj.items()
            if v is not None and v != [] and v != {}
        }
    if isinstance(obj, list):
        return [_clean_object(item) for item in obj if item is not None]
    return obj


def _pick_by_schema(obj: Any, schema: dict) -> dict:
    """Extract only the fields specified in the schema."""
    if not isinstance(obj, dict):
        return obj
    result = {}
    for key, spec in schema.items():
        if key not in obj:
            continue
        val = obj[key]
        if spec is True:
            result[key] = val
        elif isinstance(spec, dict) and isinstance(val, dict):
            result[key] = _pick_by_schema(val, spec)
        elif isinstance(spec, dict) and isinstance(val, list):
            result[key] = [_pick_by_schema(item, spec) if isinstance(item, dict) else item for item in val]
        else:
            result[key] = val
    return result


def _flatten_arrays(obj: Any) -> Any:
    """Flatten single-element arrays and join string arrays."""
    if isinstance(obj, list):
        if len(obj) == 1:
            return _flatten_arrays(obj[0])
        if all(isinstance(item, str) for item in obj):
            return ", ".join(obj)
        return [_flatten_arrays(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _flatten_arrays(v) for k, v in obj.items()}
    return obj


SEARCH_RESULT_SCHEMA = {
    "demandStayListing": {
        "id": True,
        "description": True,
        "location": True,
    },
    "badges": {"text": True},
    "structuredContent": {
        "mapSecondaryLine": {"body": True},
        "primaryLine": {"body": True},
        "secondaryLine": {"body": True},
    },
    "avgRatingA11yLabel": True,
    "structuredDisplayPrice": {
        "primaryLine": {"accessibilityLabel": True},
        "secondaryLine": {"accessibilityLabel": True},
        "explanationData": {
            "title": True,
            "priceDetails": {"items": {"description": True, "priceString": True}},
        },
    },
}

LISTING_SECTION_SCHEMAS = {
    "LOCATION_DEFAULT": {"lat": True, "lng": True, "subtitle": True, "title": True},
    "POLICIES_DEFAULT": {
        "title": True,
        "houseRulesSections": {"title": True, "items": {"title": True}},
    },
    "HIGHLIGHTS_DEFAULT": {"highlights": {"title": True}},
    "DESCRIPTION_DEFAULT": {"htmlDescription": {"htmlText": True}},
    "AMENITIES_DEFAULT": {
        "title": True,
        "seeAllAmenitiesGroups": {"title": True, "amenities": {"title": True}},
    },
}


def search_airbnb(
    location: str,
    place_id: Optional[str] = None,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    cursor: Optional[str] = None,
) -> dict:
    """Search Airbnb listings."""
    params: dict[str, Any] = {}
    if place_id:
        params["place_id"] = place_id
    if checkin:
        params["checkin"] = checkin
    if checkout:
        params["checkout"] = checkout
    if adults + children > 0:
        params["adults"] = adults
        params["children"] = children
        params["infants"] = infants
        params["pets"] = pets
    if min_price is not None:
        params["price_min"] = min_price
    if max_price is not None:
        params["price_max"] = max_price
    if cursor:
        params["cursor"] = cursor

    search_url = f"{BASE_URL}/s/{quote(location)}/homes"
    if params:
        search_url += "?" + urlencode(params)

    html = _fetch(search_url)
    data = _extract_json_data(html)
    client_data = data["niobeClientData"][0][1]
    results = client_data["data"]["presentation"]["staysSearch"]["results"]
    results = _clean_object(results)

    search_results = []
    for result in results.get("searchResults", []):
        filtered = _flatten_arrays(_pick_by_schema(result, SEARCH_RESULT_SCHEMA))
        listing_id_b64 = (
            filtered.get("demandStayListing", {}).get("id", "")
        )
        try:
            listing_id = b64decode(listing_id_b64).decode().split(":")[1]
        except Exception:
            listing_id = listing_id_b64

        search_results.append({
            "id": listing_id,
            "url": f"{BASE_URL}/rooms/{listing_id}",
            **filtered,
        })

    return {
        "searchUrl": search_url,
        "searchResults": search_results,
        "paginationInfo": results.get("paginationInfo", {}),
    }


def get_listing_details(
    listing_id: str,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
) -> dict:
    """Get detailed info about a specific Airbnb listing."""
    params: dict[str, Any] = {}
    if checkin:
        params["check_in"] = checkin
    if checkout:
        params["check_out"] = checkout
    if adults + children > 0:
        params["adults"] = adults
        params["children"] = children
        params["infants"] = infants
        params["pets"] = pets

    listing_url = f"{BASE_URL}/rooms/{listing_id}"
    if params:
        listing_url += "?" + urlencode(params)

    html = _fetch(listing_url)
    data = _extract_json_data(html)
    client_data = data["niobeClientData"][0][1]
    sections = client_data["data"]["presentation"]["stayProductDetailPage"]["sections"]["sections"]

    details = []
    for section in sections:
        section = _clean_object(section)
        section_id = section.get("sectionId", "")
        if section_id in LISTING_SECTION_SCHEMAS:
            schema = LISTING_SECTION_SCHEMAS[section_id]
            filtered = _flatten_arrays(_pick_by_schema(section.get("section", {}), schema))
            details.append({"id": section_id, **filtered})

    return {
        "listingUrl": listing_url,
        "details": details,
    }
