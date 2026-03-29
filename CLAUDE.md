# CLAUDE.md

Instructions for Claude Code when working in this repository.

## What This Is

A unified MCP server (`travel-mcp`) that exposes 15 tools across 4 travel modules: flights, hotels, Airbnb, and public transit. Covers 37 cities with 44 transit systems. Runs on STDIO via the Model Context Protocol.

## Project Structure

```
src/travel_mcp/
  server.py              # Root FastMCP server — mounts all 4 modules
  flights.py             # Wraps fli Python API (search_flights, search_dates)
  airbnb/
    scraper.py           # Pure Python Airbnb scraper (HTTP + JSON parsing)
    tools.py             # MCP tool definitions (airbnb_search, airbnb_listing_details)
  hotels/
    tools.py             # MCP tool definition (search_hotels)
    core.py              # Patched fast-hotels logic (get_hotels, parse_response)
    local_playwright.py  # Patched Playwright fetcher (location fix, strict mode fix)
    hotels_impl.py       # HotelData, Guests, THSData models
    hotels_pb2.py        # Protobuf definitions for Google Hotels API
    schema.py            # Hotel, Result dataclasses
    filter.py            # THSData filter builder
    utils.py             # IATA → city name mapping
    primp.py             # Lazy import stub (primp only needed for blocked "common" mode)
    fallback_playwright.py  # Remote Playwright fallback (non-functional, kept for reference)
  transit/
    proxy.py             # FastMCP proxy to gtfs-mcp Node.js subprocess
    loader.py            # Merges cities/*.json into a single gtfs-mcp config

cities/                  # One JSON file per city — auto-merged at startup
  README.md              # How to add new cities
  lisbon.json, rome.json, tokyo.json, ...  (37 cities)
```

## How to Run

```bash
# Start the MCP server on STDIO
PYTHONPATH=src python3 -m travel_mcp.server

# Or via the entry point (after pip install -e .)
travel-mcp
```

## How to Test

```bash
# Verify all 15 tools load and all transit systems are configured
PYTHONPATH=src python3 -c "
from travel_mcp.server import app
import asyncio, json
async def check():
    tools = await app.list_tools()
    for t in tools:
        print(f'  {t.name}')
    print(f'Total: {len(tools)} tools')
    r = await app.call_tool('list_systems', {})
    systems = json.loads(r.content[0].text)
    print(f'Transit systems: {len(systems)}')
asyncio.run(check())
"
```

Expected: 15 tools, 44 transit systems. If transit is unavailable, run `./scripts/setup-gtfs.sh`.

## Key Dependencies

- **fli** (`pip install flights`) — Google Flights API
- **fastmcp** 3.1.1 — MCP server framework (transitive via fli)
- **playwright** — headless Chromium for hotel search (`playwright install chromium`)
- **gtfs-mcp** — Node.js subprocess at `$GTFS_MCP_DIR` (default `~/Development/gtfs-mcp`)

## Important Patterns

### Module Mounting

Each module creates its own `FastMCP` instance and is mounted in `server.py`:
- Tools appear as top-level (no namespacing)
- Each module fails independently without breaking others
- `_mount_*()` functions catch exceptions and log warnings

### Hotels Module is Vendored + Patched

The `hotels/` directory is a vendored copy of `fast-hotels` v0.2.1 with three patches:
1. `local_playwright.py` — passes location to URL, waits for `.first` element
2. `core.py` — passes location to local_playwright_fetch, multi-currency price regex (`€£¥₹` + `MAD/EUR/USD/GBP`)
3. `primp.py` — lazy import to avoid crash when primp is not installed

**Do not update from upstream** without re-applying these patches.

### Airbnb is a Python Port

`airbnb/scraper.py` is a pure Python port of `@openbnb/mcp-server-airbnb`:
1. Fetches Airbnb HTML with custom User-Agent
2. Finds `#data-deferred-state-0` script tag
3. Parses embedded JSON (`niobeClientData[0][1].data.presentation...`)
4. Applies schema filtering and extracts listing data

If Airbnb changes their HTML, update `_extract_json_data()` and the JSON path in `scraper.py`.

### Transit is a Proxy with Auto-Merged City Configs

Transit tools are proxied to gtfs-mcp (Node.js) via `fastmcp.server.create_proxy()` + `NodeStdioTransport`. At startup, `transit/loader.py` reads all `cities/*.json` files and merges them into a single gtfs-mcp config.

**To add a city:** create `cities/<city-name>.json` — no code changes needed.

## Common Tasks

### Add a New Transit City

1. Find the city's GTFS feed at [mobilitydatabase.org](https://mobilitydatabase.org/) or [transit.land](https://www.transit.land/)
2. Create `cities/<city-name>.json` following the template in `cities/README.md`
3. Restart the server — data downloads on first query

### Debug Module Loading

```python
import logging
logging.basicConfig(level=logging.INFO)
from travel_mcp.server import app
```

### Verify City Configs

```bash
PYTHONPATH=src python3 -m travel_mcp.transit.loader
```

Prints merged config and lists all cities with system IDs and realtime status.
