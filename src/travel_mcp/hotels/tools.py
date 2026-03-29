"""MCP tool definitions for hotel search."""

from typing import Optional

from fastmcp import FastMCP

hotels_mcp = FastMCP("hotels")


@hotels_mcp.tool()
def search_hotels(
    location: str,
    checkin: str,
    checkout: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
    sort_by: Optional[str] = "price",
    limit: int = 20,
) -> dict:
    """Search for hotels at a location using Google Hotels data.

    Args:
        location: City name or IATA airport code (e.g., 'Marrakech', 'BCN')
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        adults: Number of adults (default: 1)
        children: Number of children (default: 0)
        infants: Number of infants (default: 0)
        room_type: Room type: 'standard', 'deluxe', or 'suite'
        sort_by: Sort by: 'price', 'rating', or null for value ratio
        limit: Maximum results (default: 20)
    """
    from .core import get_hotels
    from .hotels_impl import HotelData, Guests

    hotel_data = [HotelData(
        checkin_date=checkin,
        checkout_date=checkout,
        location=location,
        room_type=room_type,
    )]
    guests = Guests(adults=adults, children=children, infants=infants)

    result = get_hotels(
        hotel_data=hotel_data,
        guests=guests,
        fetch_mode="local",
        sort_by=sort_by,
        limit=limit,
        room_type=room_type,
    )

    return {
        "hotels": [
            {
                "name": h.name.strip() if h.name else "Unknown",
                "price_per_night": h.price,
                "rating": h.rating,
                "amenities": h.amenities,
                "url": h.url,
            }
            for h in result.hotels
        ],
        "lowest_price": result.lowest_price,
        "count": len(result.hotels),
    }
