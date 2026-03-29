"""Unified travel MCP server.

Composes flights (fli), hotels (Google Hotels), Airbnb, and public transit
into a single MCP server.
"""

import logging
import sys

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

app = FastMCP(
    "travel-mcp",
    instructions=(
        "A unified travel planning server. Use search_flights/search_dates for flights, "
        "search_hotels for hotels, airbnb_search/airbnb_listing_details for Airbnb, "
        "and transit tools (list_systems, search_stops, get_arrivals, etc.) for local transport."
    ),
)


def _mount_flights():
    """Mount flight search tools (wraps fli Python API)."""
    try:
        from travel_mcp.flights import flights_mcp
        app.mount(flights_mcp)
        logger.info("Flights module loaded (fli)")
    except ImportError:
        logger.warning("fli not installed — flight tools unavailable. pip install flights")


def _mount_hotels():
    """Mount hotel search tools."""
    try:
        from travel_mcp.hotels.tools import hotels_mcp
        app.mount(hotels_mcp)
        logger.info("Hotels module loaded (Google Hotels)")
    except Exception as e:
        logger.warning(f"Hotels module failed to load: {e}")


def _mount_airbnb():
    """Mount Airbnb search tools."""
    try:
        from travel_mcp.airbnb.tools import airbnb_mcp
        app.mount(airbnb_mcp)
        logger.info("Airbnb module loaded")
    except Exception as e:
        logger.warning(f"Airbnb module failed to load: {e}")


def _mount_transit():
    """Mount transit proxy (gtfs-mcp Node.js subprocess)."""
    try:
        from travel_mcp.transit.proxy import create_transit_proxy
        transit_mcp = create_transit_proxy()
        app.mount(transit_mcp)
        logger.info("Transit module loaded (gtfs-mcp)")
    except FileNotFoundError as e:
        logger.warning(f"Transit module not available: {e}")
    except Exception as e:
        logger.warning(f"Transit module failed to load: {e}")


# Mount all modules — each one fails gracefully if dependencies are missing
_mount_flights()
_mount_hotels()
_mount_airbnb()
_mount_transit()


def main():
    """Entry point for the travel-mcp CLI command."""
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
