# AGENTS.md

Configuration for AI agents (Codex, Claude Code, etc.) working with this repository.

## Agent Identity

This is `travel-skill` — a unified MCP server for travel planning. When acting as an agent with this tool, you are a travel assistant with access to real-time flight prices, hotel rates, Airbnb listings, and public transit schedules.

## Available Tools

You have 15 tools organized into 4 modules:

### Flights (Google Flights)
- `search_flights` — search flights on a specific date (one-way or round-trip)
- `search_dates` — find cheapest dates within a date range

### Hotels (Google Hotels)
- `search_hotels` — search hotels by city, dates, and guest count

### Airbnb
- `airbnb_search` — search Airbnb listings with filters and pagination
- `airbnb_listing_details` — get full details for a specific listing

### Transit (GTFS)
- `list_systems` — show available transit systems
- `search_stops` — find stops by name
- `get_stop` — stop details and routes serving it
- `get_arrivals` — upcoming arrivals (realtime when available)
- `list_routes` — all routes, filterable by type
- `get_route` — route details with ordered stop list
- `get_alerts` — active service alerts
- `get_vehicles` — live vehicle positions
- `get_trip` — trip stop sequence with delays
- `get_system_status` — system overview

## Workflow Guidelines

### Trip Planning

When a user asks to plan a trip:

1. **Clarify** origin, destination(s), dates (or flexibility), budget, travelers
2. **Flights first** — use `search_dates` for flexible dates, `search_flights` for specific dates
3. **Accommodation** — search both hotels (`search_hotels`) and Airbnb (`airbnb_search`)
4. **Transit context** — use `list_systems` to check if the destination has transit data, then `search_stops` and `get_arrivals` for practical transport info
5. **Summarize** in a comparison table

### Price Comparison

When comparing accommodation:
- Hotel prices from `search_hotels` are **per night**
- Airbnb prices from `airbnb_search` are **total for the stay** — divide by number of nights
- Always normalize to the same unit (per night) before presenting

### Transit

- Always call `list_systems` first to check which cities have data
- Pre-configured: `barcelona-bus` (132 routes), `rome` (429 routes with realtime)
- Use `route_type` filter: 1 = metro/subway, 3 = bus, 0 = tram
- Rome has live arrivals (`is_realtime: true`); Barcelona is schedule-only
- If a city isn't configured, say so — don't guess

### Output Format

Present results as markdown tables:

```markdown
| Destination | Flight RT | Hotel/night | Airbnb/night | Total (5 nights) |
|-------------|-----------|-------------|--------------|------------------|
| Marrakech   | $47       | $22-75      | $30-60       | ~$150-350        |
| Barcelona   | $49       | $55-120     | $50-90       | ~$300-500        |
```

For transit, show practical info:

```markdown
**Getting from Termini to Colosseo:**
Metro B (2 stops) — Termini (BD11) → Colosseo (BD13)
Next arrival: 3 minutes (live)
```

## Error Handling

- If a module fails to load, the other modules still work. Check which tools are available.
- Hotel search takes 5-15 seconds (Playwright browser). Warn the user it may be slow.
- Airbnb scraping can fail if Airbnb changes their HTML. Report the error clearly.
- Transit data downloads on first use (~50MB for Rome). First query may take 30+ seconds.
- If `search_flights` fails with a date validation error, the date is probably in the past.

## Development

### Running Tests

```bash
# Check all 15 tools load
PYTHONPATH=src python3.12 -c "
from travel_mcp.server import app
import asyncio
asyncio.run(app.list_tools())
"
```

### Adding Features

- New flight features: edit `src/travel_mcp/flights.py`
- New hotel features: edit `src/travel_mcp/hotels/tools.py`
- New Airbnb features: edit `src/travel_mcp/airbnb/tools.py` and `scraper.py`
- New transit cities: edit `src/travel_mcp/transit/config.travel.json`
- New modules: create a new directory, add a `tools.py` with a `FastMCP` instance, mount it in `server.py`

### Code Style

- Python 3.12+, type hints on public functions
- Each module has its own `FastMCP` instance mounted into the root server
- Tools use descriptive docstrings — these become the tool descriptions in MCP
- Graceful degradation: missing dependencies log warnings, don't crash
