# travel-skill

A unified [MCP](https://modelcontextprotocol.io/) server that combines **flights**, **hotels**, **Airbnb**, and **public transit** into a single interface. Built for AI assistants (Claude Desktop, Claude Code, Cursor, etc.) to plan trips end-to-end.

**15 tools. One server. Four data sources.**

| Module | Source | Tools | Data |
|--------|--------|-------|------|
| Flights | [fli](https://github.com/punitarani/fli) (Google Flights API) | `search_flights`, `search_dates` | Real-time prices, all airlines |
| Hotels | [fast-hotels](https://github.com/jongan69/hotels) (Google Hotels) | `search_hotels` | Prices, ratings, amenities |
| Airbnb | Pure Python port of [openbnb MCP](https://github.com/openbnb-org/mcp-server-airbnb) | `airbnb_search`, `airbnb_listing_details` | Listings, prices, reviews, amenities |
| Transit | [gtfs-mcp](https://github.com/jdamcd/gtfs-mcp) (GTFS feeds) | 10 tools (see below) | Schedules, live arrivals, routes |

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/JMMonte/travel-skill.git
cd travel-skill
pip install -e .
```

### 2. Install Playwright browsers (for hotel search)

```bash
playwright install chromium
```

### 3. (Optional) Set up transit

```bash
./scripts/setup-gtfs.sh
```

### 4. Run

```bash
travel-mcp
```

This starts the MCP server on STDIO. Connect it to your AI client (see [Configuration](#configuration) below).

---

## Configuration

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "travel": {
      "command": "travel-mcp"
    }
  }
}
```

### Claude Code

Add to `.claude/settings.json` or use the MCP settings:

```json
{
  "mcpServers": {
    "travel": {
      "command": "travel-mcp"
    }
  }
}
```

### Cursor / Other MCP Clients

```json
{
  "mcpServers": {
    "travel": {
      "command": "travel-mcp"
    }
  }
}
```

---

## Tools Reference

### Flights

#### `search_flights`

Search for flights between two airports on a specific date.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `origin` | string | Yes | Departure airport IATA code (e.g., `LIS`) |
| `destination` | string | Yes | Arrival airport IATA code (e.g., `BCN`) |
| `departure_date` | string | Yes | Travel date (`YYYY-MM-DD`) |
| `return_date` | string | No | Return date for round-trip |
| `departure_window` | string | No | Time window in `HH-HH` format (e.g., `6-20`) |
| `airlines` | list[str] | No | Filter by airline IATA codes (e.g., `["TP", "BA"]`) |
| `cabin_class` | string | No | `ECONOMY` (default), `PREMIUM_ECONOMY`, `BUSINESS`, `FIRST` |
| `max_stops` | string | No | `ANY` (default), `NON_STOP`, `ONE_STOP`, `TWO_PLUS_STOPS` |
| `sort_by` | string | No | `CHEAPEST` (default), `DURATION`, `DEPARTURE_TIME`, `ARRIVAL_TIME` |
| `passengers` | int | No | Number of adult passengers (default: 1) |

**Returns:** List of flights with price, duration, stops, and per-leg details (airline, flight number, airports, times).

#### `search_dates`

Find the cheapest travel dates within a date range.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `origin` | string | Yes | Departure airport IATA code |
| `destination` | string | Yes | Arrival airport IATA code |
| `start_date` | string | Yes | Start of date range (`YYYY-MM-DD`) |
| `end_date` | string | Yes | End of date range (`YYYY-MM-DD`) |
| `trip_duration` | int | No | Trip length in days (default: 3) |
| `is_round_trip` | bool | No | Round-trip search (default: false) |
| `cabin_class` | string | No | Cabin class (default: `ECONOMY`) |
| `max_stops` | string | No | Max stops (default: `ANY`) |
| `sort_by_price` | bool | No | Sort by price lowest-first (default: true) |
| `passengers` | int | No | Adult passengers (default: 1) |

**Returns:** List of dates with prices, sorted by cheapest.

---

### Hotels

#### `search_hotels`

Search for hotels using Google Hotels data.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location` | string | Yes | City name or IATA code (e.g., `Marrakech`, `BCN`) |
| `checkin` | string | Yes | Check-in date (`YYYY-MM-DD`) |
| `checkout` | string | Yes | Check-out date (`YYYY-MM-DD`) |
| `adults` | int | No | Number of adults (default: 1) |
| `children` | int | No | Number of children (default: 0) |
| `infants` | int | No | Number of infants (default: 0) |
| `room_type` | string | No | `standard` (default), `deluxe`, `suite` |
| `sort_by` | string | No | `price` (default), `rating`, or null for value ratio |
| `limit` | int | No | Max results (default: 20) |

**Returns:** List of hotels with name, price per night, rating, amenities, and Google Hotels URL.

> **Note:** Hotel search uses Playwright (headless Chromium) to bypass Google's consent wall. First run downloads the browser (~160MB). Searches take 5-15 seconds.

---

### Airbnb

#### `airbnb_search`

Search for Airbnb listings with filters and pagination.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location` | string | Yes | Location (e.g., `Marrakech, Morocco`) |
| `checkin` | string | No | Check-in date (`YYYY-MM-DD`) |
| `checkout` | string | No | Check-out date (`YYYY-MM-DD`) |
| `adults` | int | No | Number of adults (default: 1) |
| `children` | int | No | Number of children (default: 0) |
| `infants` | int | No | Number of infants (default: 0) |
| `pets` | int | No | Number of pets (default: 0) |
| `min_price` | int | No | Minimum total price for the stay |
| `max_price` | int | No | Maximum total price for the stay |
| `cursor` | string | No | Pagination cursor from previous response |

**Returns:** List of listings with name, price (total for stay), rating, reviews, badges (Superhost/Guest favorite), coordinates, and direct Airbnb URLs. 18 results per page with pagination cursors.

> **Note:** Airbnb prices are **total for the stay**, not per-night. Divide by number of nights for comparison with hotel prices.

#### `airbnb_listing_details`

Get full details about a specific Airbnb listing.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Listing ID (from search results) |
| `checkin` | string | No | Check-in date (`YYYY-MM-DD`) |
| `checkout` | string | No | Check-out date (`YYYY-MM-DD`) |
| `adults` | int | No | Number of adults (default: 1) |
| `children` | int | No | Number of children (default: 0) |
| `infants` | int | No | Number of infants (default: 0) |
| `pets` | int | No | Number of pets (default: 0) |

**Returns:** Location coordinates, house rules (check-in/out times, max guests), highlights, full description, and grouped amenities (bathroom, kitchen, parking, etc.).

---

### Transit

Transit tools query GTFS public transport data via the [gtfs-mcp](https://github.com/jdamcd/gtfs-mcp) proxy. Pre-configured with Barcelona Bus and Rome ATAC.

All transit tools require a `system` parameter — the system ID from the config (e.g., `barcelona-bus`, `rome`).

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `list_systems` | List configured transit systems | — |
| `search_stops` | Find stops by name | `system`, `query`, `limit?` |
| `get_stop` | Stop details + routes serving it | `system`, `stop_id` |
| `get_arrivals` | Upcoming arrivals (realtime when available) | `system`, `stop_id`, `route_id?`, `limit?` |
| `list_routes` | All routes, filterable by type | `system`, `route_type?` |
| `get_route` | Route details with ordered stop list | `system`, `route_id`, `direction_id?` |
| `get_alerts` | Active service alerts | `system`, `route_id?`, `stop_id?` |
| `get_vehicles` | Live vehicle positions | `system`, `route_id?` |
| `get_trip` | Trip stop sequence with delays | `system`, `trip_id` |
| `get_system_status` | Route/stop counts, alert count, feed health | `system` |

**Route types:** 0 = tram, 1 = subway/metro, 2 = rail, 3 = bus, 4 = ferry, 5 = cable tram, 6 = gondola, 7 = funicular.

#### Pre-configured Systems

| System ID | City | Routes | Stops | Realtime |
|-----------|------|--------|-------|----------|
| `barcelona-bus` | Barcelona | 132 | 4,907 | No |
| `rome` | Rome | 429 | 8,342 | Yes (live arrivals + vehicle positions) |

#### Adding More Cities

Edit `src/travel_mcp/transit/config.travel.json` to add any city that publishes GTFS feeds:

```json
{
  "id": "my-city",
  "name": "My City Transit",
  "schedule_url": "https://example.com/gtfs.zip",
  "realtime": {
    "trip_updates": ["https://example.com/trip-updates.pb"],
    "vehicle_positions": [],
    "alerts": []
  },
  "auth": null
}
```

Find GTFS feeds at [Mobility Database](https://mobilitydatabase.org/), [Transitland](https://www.transit.land/), or [OpenMobilityData](https://transitfeeds.com/).

For feeds requiring API keys:
```json
"auth": { "type": "query_param", "param_name": "api_key", "key_env": "MY_API_KEY" }
```

---

## Architecture

```
travel-mcp (FastMCP server)
├── flights_mcp      ← wraps fli Python API directly
├── hotels_mcp       ← vendored + patched fast-hotels (Playwright)
├── airbnb_mcp       ← pure Python port (requests + HTML parsing)
└── transit_proxy     ← FastMCP proxy → gtfs-mcp Node.js subprocess
```

Each module is mounted into the root server via `FastMCP.mount()`. Modules fail gracefully — if a dependency is missing, the other modules still work.

### Data Flow

- **Flights & Dates:** Python → fli → Google Flights internal API (protobuf) → structured results
- **Hotels:** Python → Playwright (headless Chrome) → Google Hotels HTML → parsed results
- **Airbnb:** Python → HTTP request → Airbnb HTML → embedded JSON (`#data-deferred-state-0`) → structured results
- **Transit:** Python → FastMCP proxy → Node.js gtfs-mcp subprocess → GTFS SQLite + realtime protobuf feeds

### Key Design Decisions

1. **Flights:** Wraps fli's Python API directly instead of mounting fli's MCP server (which uses an incompatible FastMCP subclass).
2. **Hotels:** Vendored with patches applied (upstream fast-hotels v0.2.1 has bugs: missing location in URL, CSS selector crash, USD-only price parsing).
3. **Airbnb:** Ported from Node.js to pure Python — eliminates the Node.js dependency for this module. Same logic: fetch HTML, parse embedded JSON.
4. **Transit:** Proxied via `FastMCP.create_proxy()` + `NodeStdioTransport` — gtfs-mcp is complex (SQLite + protobuf) and better left as-is.

---

## Dependencies

### Required

| Package | Purpose |
|---------|---------|
| `flights` (fli) | Google Flights search |
| `fastmcp` | MCP server framework (transitive via fli) |
| `requests` | HTTP client for Airbnb |
| `selectolax` | HTML parsing for Airbnb and Hotels |
| `playwright` | Headless browser for Hotels |

### Optional

| Package | Purpose |
|---------|---------|
| `primp` | Chrome impersonation for Hotels "common" mode (blocked, not needed) |
| Node.js 18+ | Required only for transit (gtfs-mcp subprocess) |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GTFS_MCP_DIR` | `/tmp/gtfs-mcp` | Path to gtfs-mcp installation |

---

## Limitations

- **Hotels** search takes 5-15 seconds (Playwright browser launch).
- **Airbnb** HTML parsing may break if Airbnb changes their page structure.
- **Transit** requires Node.js and a separate gtfs-mcp installation.
- **Hotels** prices may be in local currency (EUR, MAD, etc.) depending on Google's geo-detection.
- **Airbnb** prices are totals for the stay, not per-night.
- **Transit** GTFS data downloads on first use (~50MB for Rome). Cached in SQLite.
- No Marrakech transit data (no GTFS feed exists).
- Barcelona TMB metro GTFS requires an API key (only bus is pre-configured).

---

## Credits

This project composes several open-source tools:

- [fli](https://github.com/punitarani/fli) by Punit Arani — Google Flights Python library
- [fast-hotels](https://github.com/jongan69/hotels) by Jonathan Gan — Google Hotels scraper
- [mcp-server-airbnb](https://github.com/openbnb-org/mcp-server-airbnb) by OpenBnB — Airbnb MCP server (ported to Python)
- [gtfs-mcp](https://github.com/jdamcd/gtfs-mcp) by Jamie McDonald — GTFS transit MCP server
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server framework

## License

MIT
