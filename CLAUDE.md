# CLAUDE.md

Instructions for Claude Code when working in this repository.

## What This Is

A unified MCP server (`travel-mcp`) that exposes 15 tools across 4 travel modules: flights, hotels, Airbnb, and public transit. It runs on STDIO and is designed to be used by AI assistants via the Model Context Protocol.

## Project Structure

```
src/travel_mcp/
  server.py          # Root FastMCP server — mounts all 4 modules
  flights.py         # Wraps fli Python API (search_flights, search_dates)
  airbnb/
    scraper.py       # Pure Python Airbnb scraper (HTTP + JSON parsing)
    tools.py         # MCP tool definitions (airbnb_search, airbnb_listing_details)
  hotels/
    tools.py         # MCP tool definition (search_hotels)
    core.py          # Patched fast-hotels logic (get_hotels, parse_response)
    local_playwright.py  # Patched Playwright fetcher (location fix, strict mode fix)
    hotels_impl.py   # HotelData, Guests, THSData models
    hotels_pb2.py    # Protobuf definitions for Google Hotels API
    schema.py        # Hotel, Result dataclasses
    filter.py        # THSData filter builder
    utils.py         # IATA → city name mapping
    primp.py         # Lazy import stub (primp only needed for blocked "common" mode)
    fallback_playwright.py  # Remote Playwright fallback (non-functional, kept for reference)
  transit/
    proxy.py         # FastMCP proxy to gtfs-mcp Node.js subprocess
    config.travel.json  # GTFS feed config (Barcelona Bus + Rome ATAC)
```

## How to Run

```bash
# Start the MCP server on STDIO
PYTHONPATH=src python3.12 -m travel_mcp.server

# Or via the entry point (after pip install -e .)
travel-mcp
```

Use `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12` if the system python3 doesn't have the dependencies.

## How to Test

```bash
# Verify all 15 tools load
PYTHONPATH=src python3.12 -c "
from travel_mcp.server import app
import asyncio
async def check():
    tools = await app.list_tools()
    for t in tools:
        print(f'  {t.name}')
    print(f'Total: {len(tools)} tools')
asyncio.run(check())
"
```

Expected output: 15 tools (2 flights + 1 hotels + 2 airbnb + 10 transit).

If transit shows as unavailable, run `./scripts/setup-gtfs.sh` first.

## Key Dependencies

- **fli** (`pip install flights`) — provides the Google Flights API. Installed in user site-packages.
- **fastmcp** 3.1.1 — MCP server framework. Transitive dependency of fli.
- **playwright** — headless Chromium for hotel search. Run `playwright install chromium` once.
- **gtfs-mcp** — Node.js subprocess at `/tmp/gtfs-mcp/`. Run `./scripts/setup-gtfs.sh` to set up.

## Important Patterns

### Module Mounting

Each module creates its own `FastMCP` instance and is mounted into the root server in `server.py`. This means:
- Tools from all modules appear as top-level tools (no namespacing)
- Each module can fail independently without breaking others
- The `_mount_*()` functions catch exceptions and log warnings

### Hotels Module is Vendored + Patched

The `hotels/` directory is a vendored copy of `fast-hotels` v0.2.1 with three patches applied:
1. `local_playwright.py` — passes location to URL, waits for `.first` element instead of strict mode
2. `core.py` — passes location to local_playwright_fetch, multi-currency price regex
3. `primp.py` — lazy import to avoid crashing when primp is not installed

**Do not update from upstream** without re-applying these patches.

### Airbnb is a Python Port

`airbnb/scraper.py` is a pure Python port of the Node.js `@openbnb/mcp-server-airbnb`. It:
1. Fetches Airbnb HTML with a custom User-Agent
2. Finds the `#data-deferred-state-0` script tag
3. Parses the embedded JSON (`niobeClientData[0][1].data.presentation...`)
4. Applies schema filtering and extracts listing data

If Airbnb changes their HTML structure, `scraper.py` will need updating. The key markers are the `#data-deferred-state-0` element ID and the `niobeClientData` JSON path.

### Transit is a Proxy

Transit tools are proxied to a Node.js subprocess (gtfs-mcp) via `fastmcp.server.create_proxy()` + `NodeStdioTransport`. The subprocess manages SQLite databases of GTFS schedules and fetches realtime protobuf feeds.

The GTFS config file at `transit/config.travel.json` defines which cities are available. Edit this to add new cities.

## Common Tasks

### Add a New Transit City

1. Find the city's GTFS feed URL at [mobilitydatabase.org](https://mobilitydatabase.org/)
2. Add an entry to `src/travel_mcp/transit/config.travel.json`
3. Restart the server — data downloads automatically on first query (~30s for large feeds)

### Update the Airbnb Scraper

If Airbnb changes their HTML:
1. Fetch an Airbnb search page manually and inspect the HTML
2. Look for the script tag with embedded JSON data (currently `#data-deferred-state-0`)
3. Update `_extract_json_data()` in `airbnb/scraper.py`
4. Check the JSON path to search results (currently `niobeClientData[0][1].data.presentation.staysSearch.results`)

### Debug Module Loading

Set logging to see which modules load or fail:

```python
import logging
logging.basicConfig(level=logging.INFO)
from travel_mcp.server import app
```
