# travel-skill

A unified [MCP](https://modelcontextprotocol.io/) server that combines **flights**, **hotels**, **Airbnb**, and **public transit** into a single interface. Built for AI assistants (Claude Desktop, Claude Code, Cursor, etc.) to plan trips end-to-end.

**15 tools. One server. Four data sources. 37 cities.**

| Module | Source | Tools | Data |
|--------|--------|-------|------|
| Flights | [fli](https://github.com/punitarani/fli) (Google Flights API) | `search_flights`, `search_dates` | Real-time prices, all airlines |
| Hotels | [fast-hotels](https://github.com/jongan69/hotels) (Google Hotels) | `search_hotels` | Prices, ratings, amenities |
| Airbnb | Pure Python port of [openbnb MCP](https://github.com/openbnb-org/mcp-server-airbnb) | `airbnb_search`, `airbnb_listing_details` | Listings, prices, reviews, amenities |
| Transit | [gtfs-mcp](https://github.com/jdamcd/gtfs-mcp) (GTFS feeds) | 10 tools (see below) | Schedules, live arrivals, 44 systems |

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
| `adults` | int | No | Adult passengers (default: 1) |
| `children` | int | No | Child passengers (default: 0) |
| `infants_in_seat` | int | No | Infants in seat (default: 0) |
| `infants_on_lap` | int | No | Infants on lap (default: 0) |
| `max_price` | int | No | Maximum price in USD |
| `max_duration` | int | No | Maximum total flight duration in minutes |
| `layover_airports` | list[str] | No | Restrict layovers to these airports |
| `max_layover_duration` | int | No | Maximum layover duration in minutes |
| `top_n` | int | No | Round-trip search depth (default: 5) |

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
| `airlines` | list[str] | No | Filter by airline IATA codes |
| `cabin_class` | string | No | Cabin class (default: `ECONOMY`) |
| `max_stops` | string | No | Max stops (default: `ANY`) |
| `departure_window` | string | No | Time window in `HH-HH` format |
| `sort_by_price` | bool | No | Sort by price lowest-first (default: true) |
| `adults` | int | No | Adult passengers (default: 1) |
| `children` | int | No | Child passengers (default: 0) |
| `infants_in_seat` | int | No | Infants in seat (default: 0) |
| `infants_on_lap` | int | No | Infants on lap (default: 0) |
| `days_of_week` | list[str] | No | Filter by departure day (e.g., `["friday", "saturday"]`) |

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
| `place_id` | string | No | Google Maps Place ID for precise location targeting |
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

Transit tools query GTFS public transport data via the [gtfs-mcp](https://github.com/jdamcd/gtfs-mcp) proxy. Pre-configured with **37 cities and 44 transit systems** across Europe, Asia, and the Americas.

All transit tools require a `system` parameter — the system ID from the config (e.g., `lisbon-carris`, `rome`, `tokyo-metro`).

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `list_systems` | List all 44 configured transit systems | — |
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

#### City Coverage

<details>
<summary><strong>Europe — 21 cities, 21 systems</strong></summary>

| City | System ID | Modes | Realtime | Auth |
|------|-----------|-------|----------|------|
| Amsterdam | `ovapi-netherlands` | All Dutch transit (bus/tram/metro/train) | No | None |
| Barcelona | `barcelona-bus` | Metropolitan bus | No | None |
| Berlin | `vbb` | U-Bahn, S-Bahn, tram, bus | No | None |
| Brussels | `stib-mivb` | Metro, tram, bus | No | None |
| Budapest | `bkk` | Metro, tram, trolleybus, bus | Yes | API key |
| Copenhagen | `rejseplanen` | All Denmark transit | No | None |
| Dublin | `nta` | Bus, Luas, rail (all Ireland) | Yes | API key |
| Helsinki | `hsl` | Metro, tram, bus, rail, ferry | Yes | None |
| Israel | `israel-transit` | Nationwide bus, rail, light rail | No | None |
| Lisbon | `lisbon-carris` | Carris Metropolitana bus/tram | Yes | None |
| London | `london-bus` | All London buses (TfL/BODS) | No | None |
| Madrid | `crtm-metro` | Metro de Madrid | No | None |
| Milan | `atm-milan` | Metro, tram, bus | No | None |
| Munich | `mvv` | U-Bahn, S-Bahn, tram, bus, regional | No | None |
| Oslo | `entur-norway` | All Norway transit (60 operators) | Yes | None |
| Paris | `idfm` | Metro, RER, tram, bus (all Ile-de-France) | No | None |
| Porto | `stcp` | Bus, tram | No | None |
| Prague | `pid` | Metro, tram, bus, funicular, ferry | Yes | API key (RT only) |
| Rome | `rome` | Metro, bus, tram | Yes | None |
| Vienna | `wiener-linien` | U-Bahn, tram, bus | No | None |
| Warsaw | `ztm-warsaw` | Metro, tram, bus | Yes | None |

</details>

<details>
<summary><strong>Asia — 9 cities, 13 systems</strong></summary>

| City | System ID | Modes | Realtime | Auth |
|------|-----------|-------|----------|------|
| Dubai | `dubai-rta` | Metro, tram, bus | No | None |
| Hong Kong | `hk-transport` | MTR, bus, tram, ferry | No | None |
| Jakarta | `transjakarta` | BRT, feeder routes | No | None |
| Kochi | `kochi-metro` | Metro (single line) | No | None |
| Kuala Lumpur | `kl-rail` | LRT, MRT, Monorail | No | None |
| | `kl-bus` | Rapid Bus | Yes | None |
| | `kl-ktmb` | KTMB Komuter + ETS rail | Yes | None |
| Manila | `manila-transit` | LRT, MRT, PNR, bus | No | None |
| Singapore | `sg-transit` | Bus + MRT/LRT (community) | No | None |
| Taipei | `taipei-metro` | Metro MRT | No | API key |
| Tokyo | `toei-rail` | Toei Subway, tram, Liner | Yes | API key |
| | `toei-bus` | Toei municipal buses | Yes | None (static) |
| | `tokyo-metro` | 9 subway lines | Yes | API key |

</details>

<details>
<summary><strong>Americas — 7 cities, 10 systems</strong></summary>

| City | System ID | Modes | Realtime | Auth |
|------|-----------|-------|----------|------|
| Chicago | `cta` | L train, bus | No | None |
| Los Angeles | `la-metro-bus` | Metro bus | No | None |
| | `la-metro-rail` | Metro rail | No | None |
| Mexico City | `cdmx-semovi` | Metro, Metrobus, tram, bus, cable | No | None |
| New York | `nyc-subway` | Subway (MTA) | Yes | None |
| San Francisco | `bart` | BART rapid transit | No | None |
| | `muni` | Muni bus, light rail, cable car | No | None |
| Toronto | `ttc` | Subway, bus, streetcar | Yes | None |
| Washington DC | `wmata-bus` | Metrobus | Yes | API key |
| | `wmata-rail` | Metrorail | Yes | API key |

</details>

#### Adding More Cities

Create a new file in `cities/<city-name>.json`:

```json
{
  "city": "City Name",
  "country": "XX",
  "systems": [
    {
      "id": "city-system",
      "name": "System Name (modes)",
      "schedule_url": "https://example.com/gtfs.zip",
      "realtime": {
        "trip_updates": [],
        "vehicle_positions": ["https://example.com/vehicles.pb"],
        "alerts": []
      },
      "auth": null
    }
  ]
}
```

All city configs are automatically merged at startup. **No code changes needed** — just add the JSON file and restart.

Find GTFS feeds at [Mobility Database](https://mobilitydatabase.org/), [Transitland](https://www.transit.land/), or city open data portals.

For feeds requiring API keys:
```json
"auth": { "type": "query_param", "param_name": "api_key", "key_env": "MY_API_KEY" }
```

See [`cities/README.md`](cities/README.md) for full contribution guide.

---

## Architecture

```
travel-mcp (FastMCP server)
├── flights_mcp      ← wraps fli Python API directly
├── hotels_mcp       ← vendored + patched fast-hotels (Playwright)
├── airbnb_mcp       ← pure Python port (requests + HTML parsing)
└── transit_proxy     ← FastMCP proxy → gtfs-mcp Node.js subprocess
                       ↑ auto-merges cities/*.json at startup
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
4. **Transit:** Proxied via `fastmcp.server.create_proxy()` + `NodeStdioTransport` — gtfs-mcp is complex (SQLite + protobuf) and better left as-is. City configs in `cities/` are auto-merged into a single gtfs-mcp config at startup.

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
| `GTFS_MCP_DIR` | `~/Development/gtfs-mcp` | Path to gtfs-mcp installation |
| `TRAVEL_MCP_DATA_DIR` | `~/Development/gtfs-mcp/data` | Where GTFS SQLite databases are cached |
| `ODPT_CONSUMER_KEY` | — | Tokyo Metro/Toei realtime (free at [developer.odpt.org](https://developer.odpt.org/)) |
| `BKK_API_KEY` | — | Budapest BKK realtime (free at [opendata.bkk.hu](https://opendata.bkk.hu)) |
| `NTA_API_KEY` | — | Dublin NTA realtime (free at [developer.nationaltransport.ie](https://developer.nationaltransport.ie)) |
| `WMATA_API_KEY` | — | Washington DC WMATA (free at [developer.wmata.com](https://developer.wmata.com)) |
| `TDX_ACCESS_TOKEN` | — | Taipei MRT (free at [tdx.transportdata.tw](https://tdx.transportdata.tw)) |
| `GOLEMIO_API_KEY` | — | Prague realtime (free at [api.golemio.cz](https://api.golemio.cz)) |

API keys are only needed for realtime data in those specific cities. Static schedules work without any keys.

---

## Limitations

- **Hotels** search takes 5-15 seconds (Playwright browser launch).
- **Airbnb** HTML parsing may break if Airbnb changes their page structure.
- **Transit** requires Node.js and a separate gtfs-mcp installation.
- **Hotels** prices may be in local currency depending on Google's geo-detection.
- **Airbnb** prices are totals for the stay, not per-night.
- **Transit** GTFS data downloads on first use per city (5-90MB). Cached in SQLite.
- Some cities not available: Seoul, Bangkok, Osaka, Beijing/Shanghai, HCMC (no GTFS published).
- Some feeds may require free API keys for realtime data (see Environment Variables above).

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
