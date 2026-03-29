"""MCP tool definitions for Airbnb search."""

from typing import Optional

from fastmcp import FastMCP

airbnb_mcp = FastMCP("airbnb")


@airbnb_mcp.tool()
def airbnb_search(
    location: str,
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
    """Search for Airbnb listings with various filters and pagination.

    Args:
        location: Location to search (e.g., "Marrakech, Morocco", "Barcelona, Spain")
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        adults: Number of adults (default: 1)
        children: Number of children (default: 0)
        infants: Number of infants (default: 0)
        pets: Number of pets (default: 0)
        min_price: Minimum total price for the stay
        max_price: Maximum total price for the stay
        cursor: Base64-encoded pagination cursor from previous response
    """
    from .scraper import search_airbnb

    return search_airbnb(
        location=location,
        checkin=checkin,
        checkout=checkout,
        adults=adults,
        children=children,
        infants=infants,
        pets=pets,
        min_price=min_price,
        max_price=max_price,
        cursor=cursor,
    )


@airbnb_mcp.tool()
def airbnb_listing_details(
    id: str,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
) -> dict:
    """Get detailed information about a specific Airbnb listing.

    Returns location, house rules, highlights, description, and amenities.

    Args:
        id: Airbnb listing ID (from search results)
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        adults: Number of adults (default: 1)
        children: Number of children (default: 0)
        infants: Number of infants (default: 0)
        pets: Number of pets (default: 0)
    """
    from .scraper import get_listing_details

    return get_listing_details(
        listing_id=id,
        checkin=checkin,
        checkout=checkout,
        adults=adults,
        children=children,
        infants=infants,
        pets=pets,
    )
