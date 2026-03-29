---
name: travel
description: "Search flights, hotels, Airbnb, and public transit for travel planning. Use when the user asks to 'find flights', 'search hotels', 'find airbnb', 'plan a trip', 'cheapest dates to fly', 'book travel', 'public transport', 'metro', 'bus routes', or mentions flight/hotel/airbnb/transit search. Combines Google Flights (fli), Google Hotels (fast-hotels), Airbnb (MCP), and GTFS transit data (gtfs-mcp)."
allowed-tools: [Bash, Read, Edit, Write, WebSearch, WebFetch]
argument-hint: "[origin] [destination] [dates]"
---

# Travel Search Skill

Search flights via **fli** (Google Flights), hotels via **fast-hotels** (Google Hotels), short-term rentals via **mcp-server-airbnb** (Airbnb), and local transit via **gtfs-mcp** (GTFS public transport data).

## Prerequisites

### fli (flights)
```bash
pip install flights
```
- CLI binary: `~/Library/Python/3.12/bin/fli`
- Python API: `from fli.search import SearchFlights, SearchDates`
- MCP servers: `fli-mcp` (STDIO) / `fli-mcp-http` (HTTP on port 8000)

### fast-hotels
```bash
pip install fast-hotels primp selectolax
```
Requires Playwright Chromium:
```bash
~/Library/Python/3.12/bin/playwright install chromium
```

**Important:** fast-hotels v0.2.1 has bugs that require patching. See Patches section.

### mcp-server-airbnb
```bash
npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt
```
Runs on STDIO. Requires Node.js 18+. No additional setup needed — npx auto-installs.

### gtfs-mcp (public transit)
```bash
cd /tmp/gtfs-mcp && npm install && npm run build
```
Cloned to `/tmp/gtfs-mcp/`. Config at `/tmp/gtfs-mcp/config.travel.json`. Requires Node.js 18+.
Pre-configured systems: Barcelona Bus (AMB), Rome ATAC (Metro/Bus/Tram with realtime).

---

## 1. Flight Search — CLI

### One-way
```bash
~/Library/Python/3.12/bin/fli flights <ORIGIN> <DEST> <DATE> [options]
```

### Round-trip
```bash
~/Library/Python/3.12/bin/fli flights <ORIGIN> <DEST> <DATE> -r <RETURN_DATE> [options]
```

### Flight options
| Flag | Description | Values |
|------|-------------|--------|
| `-r`, `--return` | Return date (YYYY-MM-DD) | date string |
| `-c`, `--class` | Cabin class | `ECONOMY`, `PREMIUM_ECONOMY`, `BUSINESS`, `FIRST` |
| `-s`, `--stops` | Max stops | `ANY`, `0` (non-stop), `1`, `2` |
| `-o`, `--sort` | Sort by | `CHEAPEST`, `DURATION`, `DEPARTURE_TIME`, `ARRIVAL_TIME`, `TOP_FLIGHTS`, `NONE` |
| `-a`, `--airlines` | Filter airlines | IATA codes (e.g., `BA KL`) |
| `-t`, `--time` | Departure window | 24h format (e.g., `6-20`) |

### Find cheapest dates over a range
```bash
~/Library/Python/3.12/bin/fli dates <ORIGIN> <DEST> [options]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--from` | Start date | tomorrow |
| `--to` | End date | ~2 months out |
| `-d` | Trip duration in days | 3 |
| `-R` | Round-trip mode | off |
| `--sort` | Sort by price (lowest first) | off |
| `--mon` through `--sun` | Filter by day of week | all days |
| `-c`, `--class` | Cabin class | `ECONOMY` |
| `-s`, `--stops` | Max stops | `ANY` |
| `-a`, `--airlines` | Filter airlines | all |
| `-time` | Departure window | all day |

### CLI examples
```bash
# Basic round trip
fli flights JFK LAX 2026-05-15 -r 2026-05-20 --sort CHEAPEST

# Non-stop business class
fli flights JFK LAX 2026-05-15 --stops 0 --class BUSINESS --sort CHEAPEST

# Morning flights only, specific airlines
fli flights LIS BCN 2026-05-22 --time 6-12 --airlines TP FR

# Cheapest 5-day round-trip dates over Apr-Jun
fli dates LIS BCN --from 2026-04-01 --to 2026-06-30 -d 5 -R --sort

# Weekend departures only
fli dates LIS RAK --from 2026-04-01 --to 2026-06-30 -d 5 -R --sort --fri --sat
```

---

## 2. Flight Search — Python API

The Python API gives structured data (Pydantic models) and more control than the CLI.

```python
import sys
sys.path.insert(0, '/Users/joaomontenegro/Library/Python/3.12/lib/python/site-packages')

from fli.search import SearchFlights, SearchDates
from fli.models import (
    FlightSearchFilters, FlightSegment, FlightResult, FlightLeg,
    DateSearchFilters,
    PassengerInfo, PriceLimit, TimeRestrictions, LayoverRestrictions,
    Airport, Airline, SeatType, SortBy, MaxStops, TripType,
)
```

### One-way flight search
```python
filters = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.LIS, 0]],
            arrival_airport=[[Airport.BCN, 0]],
            travel_date="2026-05-22",
            time_restrictions=TimeRestrictions(earliest_departure=6, latest_departure=20),
        )
    ],
    stops=MaxStops.NON_STOP,
    seat_type=SeatType.ECONOMY,
    sort_by=SortBy.CHEAPEST,
    airlines=[Airline.TP],           # Optional: filter to TAP only
    price_limit=PriceLimit(max_price=500),  # Optional: max price
    max_duration=600,                # Optional: max duration in minutes
)

search = SearchFlights()
results = search.search(filters, top_n=10)
# results: list[FlightResult]
# Each FlightResult has: .price, .duration, .stops, .legs[]
# Each FlightLeg has: .airline, .flight_number, .departure_airport, .arrival_airport,
#                     .departure_datetime, .arrival_datetime, .duration
```

### Round-trip search
```python
filters = FlightSearchFilters(
    trip_type=TripType.ROUND_TRIP,
    passenger_info=PassengerInfo(adults=2, children=1, infants_on_lap=0, infants_in_seat=0),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.LIS, 0]],
            arrival_airport=[[Airport.RAK, 0]],
            travel_date="2026-05-09",
        ),
        FlightSegment(
            departure_airport=[[Airport.RAK, 0]],
            arrival_airport=[[Airport.LIS, 0]],
            travel_date="2026-05-14",
        ),
    ],
    stops=MaxStops.ANY,
    seat_type=SeatType.ECONOMY,
    sort_by=SortBy.CHEAPEST,
)

search = SearchFlights()
results = search.search(filters, top_n=5)
# results: list[tuple[FlightResult, FlightResult]] for round trips
# Each tuple is (outbound, return)
```

### Date range search (cheapest dates)
```python
filters = DateSearchFilters(
    trip_type=TripType.ROUND_TRIP,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.LIS, 0]],
            arrival_airport=[[Airport.BCN, 0]],
            travel_date="2026-04-01",
        ),
        FlightSegment(
            departure_airport=[[Airport.BCN, 0]],
            arrival_airport=[[Airport.LIS, 0]],
            travel_date="2026-04-06",  # Must be from_date + duration
        ),
    ],
    stops=MaxStops.ANY,
    seat_type=SeatType.ECONOMY,
    from_date="2026-04-01",
    to_date="2026-06-30",
    duration=5,  # Required for round trips
)

search = SearchDates()
dates = search.search(filters)
# dates: list with .date, .price, .return_date attributes
dates.sort(key=lambda x: x.price)
```

### Key models reference
- **PassengerInfo**: `adults`, `children`, `infants_in_seat`, `infants_on_lap`
- **TimeRestrictions**: `earliest_departure`, `latest_departure`, `earliest_arrival`, `latest_arrival` (hours 0-24)
- **PriceLimit**: `max_price` (int), `currency` (default USD)
- **LayoverRestrictions**: `airports` (list[Airport]), `max_duration` (minutes)
- **SeatType**: `ECONOMY=1`, `PREMIUM_ECONOMY=2`, `BUSINESS=3`, `FIRST=4`
- **MaxStops**: `ANY=0`, `NON_STOP=1`, `ONE_STOP_OR_FEWER=2`, `TWO_OR_FEWER_STOPS=3`
- **SortBy**: `NONE=0`, `TOP_FLIGHTS=1`, `CHEAPEST=2`, `DEPARTURE_TIME=3`, `ARRIVAL_TIME=4`, `DURATION=5`
- **TripType**: `ROUND_TRIP=1`, `ONE_WAY=2` (multi-city not yet supported)
- **Airport**: Enum of IATA codes (e.g., `Airport.LIS`, `Airport.JFK`)
- **Airline**: Enum of IATA codes (e.g., `Airline.TP`, `Airline.BA`)

---

## 3. Flight Search — MCP Server

fli ships with a full MCP server for Claude Desktop / Claude Code integration.

### Setup
```bash
# STDIO mode (for Claude Desktop)
~/Library/Python/3.12/bin/fli-mcp

# HTTP mode (port 8000, for remote clients)
~/Library/Python/3.12/bin/fli-mcp-http
```

Claude Desktop config (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "fli": {
      "command": "fli-mcp"
    }
  }
}
```

### MCP Tools
- **`search_flights`** — search flights on a specific date (one-way or round-trip)
- **`search_dates`** — find cheapest dates within a date range

### MCP Prompts
- **`search-direct-flight`** — generates a tool call for direct flight search
- **`find-budget-window`** — generates a tool call for flexible date search

### MCP Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `FLI_MCP_DEFAULT_PASSENGERS` | Default passenger count | 1 |
| `FLI_MCP_DEFAULT_CURRENCY` | Currency code | USD |
| `FLI_MCP_DEFAULT_CABIN_CLASS` | Default cabin class | ECONOMY |
| `FLI_MCP_DEFAULT_SORT_BY` | Default sort | CHEAPEST |
| `FLI_MCP_DEFAULT_DEPARTURE_WINDOW` | Default time window (HH-HH) | None |
| `FLI_MCP_MAX_RESULTS` | Max results per query | None |

---

## 4. Hotel Search — fast-hotels Python API

Use `fetch_mode='local'` (Playwright-based). The default `common` mode gets blocked by Google's cookie consent wall.

```python
from fast_hotels import get_hotels
from fast_hotels.hotels_impl import HotelData, Guests

hotel_data = [HotelData(
    checkin_date='2026-05-09',
    checkout_date='2026-05-14',
    location='Marrakech',       # City name or IATA airport code
    room_type='standard',       # Optional: 'standard', 'deluxe', 'suite'
    amenities=['wifi', 'pool'], # Optional: preferred amenities
)]
guests = Guests(adults=2, children=1, infants=0)  # max 9 total, infants <= adults

result = get_hotels(
    hotel_data=hotel_data,
    guests=guests,
    fetch_mode='local',       # MUST use 'local' — 'common' is blocked
    sort_by='price',          # 'price', 'rating', or None (default: value ratio = rating/price)
    limit=20,                 # Optional: max results
    room_type='standard',     # 'standard', 'deluxe', 'suite'
    amenities=['wifi'],       # Optional: filter by amenities
)

# Result object
result.hotels       # list[Hotel] — each has .name, .price, .rating, .amenities, .url
result.lowest_price  # float — cheapest price found
result.current_price # float — same as lowest_price

for h in result.hotels:
    rating = f'{h.rating}★' if h.rating else 'N/A'
    print(f'{h.name.strip()} — ${h.price:.0f}/night — {rating}')
    if h.url:
        print(f'  {h.url}')
    if h.amenities:
        print(f'  Amenities: {", ".join(h.amenities)}')
```

### Fetch modes
| Mode | How it works | Status |
|------|-------------|--------|
| `common` | Direct HTTP via primp (chrome impersonation) | Blocked by Google consent wall |
| `fallback` | Tries common first, falls back to remote Playwright | Remote service returns 401 |
| `force-fallback` | Forces remote Playwright | Remote service returns 401 |
| `local` | Local Playwright headless browser | **Works** (requires patching) |

### IATA code support
Locations can be IATA airport codes — they're auto-converted to city names via a global airports CSV. Example: `"HND"` → `"Tokyo"`, `"RAK"` → `"Marrakech"`.

---

## 5. Airbnb Search — MCP Server

The `@openbnb/mcp-server-airbnb` package scrapes Airbnb via Cheerio (HTML parsing, no browser needed). It runs as an MCP server over STDIO.

### Running directly via CLI (pipe MCP JSON-RPC messages)

```bash
# Send MCP protocol messages to search
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'; \
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"airbnb_search","arguments":{"location":"Marrakech, Morocco","checkin":"2026-05-09","checkout":"2026-05-14","adults":1,"maxPrice":100,"ignoreRobotsText":true}}}'; \
sleep 10) | npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt 2>/dev/null
```

### Claude Desktop / Claude Code config
```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]
    }
  }
}
```

### Tool: `airbnb_search`

Search Airbnb listings with filters. Returns 18 results per page with pagination.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location` | string | Yes | City/region (e.g., "Marrakech, Morocco", "Barcelona, Spain") |
| `placeId` | string | No | Google Maps Place ID — overrides location for precise targeting |
| `checkin` | string | No | Check-in date (YYYY-MM-DD) |
| `checkout` | string | No | Check-out date (YYYY-MM-DD) |
| `adults` | number | No | Number of adults (default: 1) |
| `children` | number | No | Number of children (default: 0) |
| `infants` | number | No | Number of infants (default: 0) |
| `pets` | number | No | Number of pets (default: 0) |
| `minPrice` | number | No | Minimum total price for the stay |
| `maxPrice` | number | No | Maximum total price for the stay |
| `cursor` | string | No | Base64-encoded pagination cursor (from previous response's `paginationInfo.nextPageCursor`) |
| `ignoreRobotsText` | boolean | No | Override robots.txt for this request |

**Returns per listing:**
- `id` — Airbnb listing ID
- `url` — Direct link (e.g., `https://www.airbnb.com/rooms/12345`)
- `demandStayListing.description.name` — Property name
- `demandStayListing.location.coordinate` — `{latitude, longitude}`
- `badges` — "Guest favorite", "Superhost", or empty
- `structuredContent.primaryLine` — Room info (e.g., "2 bedrooms, 3 beds")
- `avgRatingA11yLabel` — Rating string (e.g., "4.78 out of 5 average rating, 27 reviews")
- `structuredDisplayPrice.primaryLine.accessibilityLabel` — Total price (e.g., "€ 284 total")
- `structuredDisplayPrice.explanationData.priceDetails` — Price breakdown per night, discounts, taxes
- `paginationInfo.nextPageCursor` — Cursor for next page
- `paginationInfo.pageCursors` — Array of all page cursors (15 pages = ~270 results)

### Tool: `airbnb_listing_details`

Get full details for a specific listing.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Airbnb listing ID (from search results) |
| `checkin` | string | No | Check-in date (YYYY-MM-DD) |
| `checkout` | string | No | Check-out date (YYYY-MM-DD) |
| `adults` | number | No | Number of adults (default: 1) |
| `children` | number | No | Number of children (default: 0) |
| `infants` | number | No | Number of infants (default: 0) |
| `pets` | number | No | Number of pets (default: 0) |
| `ignoreRobotsText` | boolean | No | Override robots.txt for this request |

**Returns sections:**
- **LOCATION_DEFAULT** — `lat`, `lng`, `title` ("Where you'll be")
- **POLICIES_DEFAULT** — House rules: check-in/out times, max guests, quiet hours, pet policy, additional rules
- **HIGHLIGHTS_DEFAULT** — Key features (e.g., "Self check-in, Park for free, Superhost")
- **DESCRIPTION_DEFAULT** — Full HTML description of the property
- **AMENITIES_DEFAULT** — Grouped amenities: Bathroom, Bedroom, Entertainment, Kitchen, Parking, etc.
- Direct listing URL with date/guest parameters

### Notes
- `--ignore-robots-txt` is needed for searches (Airbnb's robots.txt blocks the search path)
- Prices are **total** for the stay, not per-night — divide by number of nights for comparison
- `roomType` filter exists in the source but is commented out (not functional in v0.1.3)
- Availability calendar data exists in the API but is not exposed (commented out in v0.1.3)
- No sorting parameter — results come in Airbnb's default relevance order
- For price sorting, parse results and sort client-side

---

## 6. Patches Required for fast-hotels v0.2.1


The installed package has bugs. After installing, apply these fixes to the venv or site-packages.

### Patch 1: `local_playwright.py` — location missing from URL + strict mode crash

Replace the entire file at `<site-packages>/fast_hotels/local_playwright.py`:

```python
from typing import Any
import asyncio
from playwright.async_api import async_playwright

async def fetch_with_playwright(url: str) -> str:
    """Local Playwright fallback for hotel scraping"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        if page.url.startswith("https://consent.google.com"):
            await page.click('text="Accept all"')
            await page.wait_for_load_state("networkidle")
        await page.locator('div.uaTTDe').first.wait_for(timeout=15000)
        body = await page.content()
        await browser.close()
    return body

def local_playwright_fetch(params: dict, location: str = "") -> Any:
    """Local Playwright fallback function"""
    from .utils import get_city_from_iata
    city = get_city_from_iata(location) if location else ""
    location_url = city.strip().replace(' ', '+').lower() if city else ""
    base = f"https://www.google.com/travel/hotels/{location_url}" if location_url else "https://www.google.com/travel/hotels"
    url = base + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    body = asyncio.run(fetch_with_playwright(url))

    class DummyResponse:
        status_code = 200
        text = body
        text_markdown = body

    return DummyResponse
```

### Patch 2: `core.py` — pass location to local mode + multi-currency price parsing

In `get_hotels_from_filter`, change:
```python
res = local_playwright_fetch(params)
```
to:
```python
res = local_playwright_fetch(params, location=location)
```

In `parse_response`, change the price regex from:
```python
price_matches = re.findall(r'\$([0-9,.]+)', card_text)
```
to:
```python
price_matches = re.findall(r'[\$€£¥₹]([0-9,.]+)', card_text)
if not price_matches:
    price_matches = re.findall(r'([0-9,.]+)\s*(?:MAD|EUR|USD|GBP)', card_text)
```

---

## 7. Public Transit — gtfs-mcp

Query GTFS static schedules and realtime feeds for any transit system. Installed at `/tmp/gtfs-mcp/`.

### Running

```bash
GTFS_MCP_CONFIG=/tmp/gtfs-mcp/config.travel.json node /tmp/gtfs-mcp/dist/index.js
```

Pipe MCP JSON-RPC messages via stdin (same pattern as Airbnb MCP):
```bash
(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'; \
echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'; \
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_stops","arguments":{"system":"rome","query":"Colosseo","limit":5}}}'; \
sleep 10) | GTFS_MCP_CONFIG=/tmp/gtfs-mcp/config.travel.json node /tmp/gtfs-mcp/dist/index.js 2>/dev/null
```

### Pre-configured systems

| System ID | Name | Routes | Stops | Realtime |
|-----------|------|--------|-------|----------|
| `barcelona-bus` | Barcelona Metropolitan Bus (AMB) | 132 | 4,907 | No |
| `rome` | Rome ATAC (Metro/Bus/Tram) | 429 | 8,342 | Yes (trip updates, vehicle positions, alerts) |

Config: `/tmp/gtfs-mcp/config.travel.json`. Data cached at `/tmp/gtfs-mcp/data/`.

### Tools (10 total)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `list_systems` | List all configured transit systems | — |
| `search_stops` | Find stops by name | `system`, `query`, `limit?` |
| `get_stop` | Stop details + routes serving it | `system`, `stop_id` |
| `get_arrivals` | Upcoming arrivals (realtime when available) | `system`, `stop_id`, `route_id?`, `limit?` |
| `list_routes` | All routes, filterable by type | `system`, `route_type?` (0=tram, 1=subway, 2=rail, 3=bus) |
| `get_route` | Route details with ordered stop list | `system`, `route_id`, `direction_id?` |
| `get_alerts` | Active service alerts | `system`, `route_id?`, `stop_id?` |
| `get_vehicles` | Live vehicle positions | `system`, `route_id?` |
| `get_trip` | Trip stop sequence with delays | `system`, `trip_id` |
| `get_system_status` | Overview: counts, alerts, feed health | `system` |

### Adding new cities

Create or edit `/tmp/gtfs-mcp/config.travel.json`:
```json
{
  "systems": [
    {
      "id": "my-city",
      "name": "My City Transit",
      "schedule_url": "https://example.com/gtfs.zip",
      "realtime": {
        "trip_updates": ["https://example.com/trip-updates.pb"],
        "vehicle_positions": ["https://example.com/vehicles.pb"],
        "alerts": ["https://example.com/alerts.pb"]
      },
      "auth": null
    }
  ],
  "data_dir": "/tmp/gtfs-mcp/data",
  "schedule_refresh_hours": 168
}
```

For feeds requiring API keys, use auth:
```json
"auth": { "type": "query_param", "param_name": "api_key", "key_env": "MY_API_KEY" }
```
or:
```json
"auth": { "type": "header", "header_name": "X-Api-Key", "key_env": "MY_API_KEY" }
```

Find GTFS feeds at:
- [Mobility Database](https://mobilitydatabase.org/) — global catalog of 6000+ feeds
- [Transitland](https://www.transit.land/) — aggregated feed directory
- [OpenMobilityData](https://transitfeeds.com/) — legacy but still useful

### Known working GTFS URLs
- Barcelona Bus (AMB): `https://www.ambmobilitat.cat/OpenData/google_transit.zip`
- Rome ATAC: `https://romamobilita.it/sites/default/files/rome_static_gtfs.zip`
- Rome RT trips: `https://romamobilita.it/sites/default/files/rome_rtgtfs_trip_updates_feed.pb`
- Rome RT vehicles: `https://romamobilita.it/sites/default/files/rome_rtgtfs_vehicle_positions_feed.pb`
- Rome RT alerts: `https://romamobilita.it/sites/default/files/rome_rtgtfs_alerts_feed.pb`
- NYC MTA Subway: use built-in `config.mta.json` (no auth needed)

### Notes
- First query per system downloads and imports the GTFS ZIP into SQLite — Rome (49MB) takes ~30s
- Data is cached at `data_dir/{system_id}/gtfs.db` and refreshes after `schedule_refresh_hours`
- Realtime feeds are fetched on-demand with 30s in-memory caching
- `get_arrivals` merges scheduled times with realtime delays automatically
- `route_type` filter: 0=tram/streetcar, 1=subway/metro, 2=rail, 3=bus, 4=ferry, 5=cable tram, 6=gondola, 7=funicular
- Barcelona TMB metro GTFS requires an API key from developer.tmb.cat (not pre-configured)
- Marrakech has no GTFS data available

---

## 8. Trip Planning Workflow

When the user wants to plan a trip:

1. **Clarify**: origin city, destination(s) or "suggest destinations", dates or flexibility, budget, number of travelers, hotel vs airbnb preference
2. **Flights first**: Use `fli dates` to scan a date range if flexible, or `fli flights` for specific dates. Always use `--sort CHEAPEST` and `-R` for round trips.
3. **Accommodation**: Search both hotels (fast-hotels) and Airbnb (MCP) for comparison.
   - Hotels: `fast-hotels` with `fetch_mode='local'` and `sort_by='price'`
   - Airbnb: pipe MCP JSON-RPC to `npx @openbnb/mcp-server-airbnb --ignore-robots-txt`
   - For Airbnb, divide total price by number of nights for per-night comparison
4. **Deep dive**: Use `airbnb_listing_details` for top picks to show amenities, house rules, and exact location.
5. **Summarize**: Present a comparison table with flight cost, accommodation options, total estimated budget.
6. **Multiple destinations**: Run hotel searches in sequence (Playwright single-threaded). Flight CLI and Airbnb searches can run in parallel.

### Output format
Present results as a markdown table:

```
| Destination | Flight RT | Hotel/night | Airbnb/night | 5-night total | Vibe |
|---|---|---|---|---|---|
| Marrakech | $47 | $22-75 | €30-60 | ~€150-350 | Riads, souks, food |
| Barcelona | $49 | $55-120 | €50-90 | ~€300-500 | Beach + city |
```

### Tips
- `fli dates` outputs ASCII price trend charts — useful for spotting patterns
- Day-of-week flags (`--fri`, `--sat`) are great for weekend trip planning
- `top_n` on `SearchFlights.search()` controls outbound→return lookup depth (default 5)
- `PriceLimit(max_price=X)` pre-filters expensive flights in the Python API
- `LayoverRestrictions(airports=[Airport.MAD], max_duration=180)` controls layover airports/time
- Hotels: `sort_by=None` (default) sorts by value ratio (rating/price) — often most useful
- Airbnb: prices are **total** for stay, not per-night — always divide for comparison
- Airbnb: use `maxPrice` to cap results; no server-side sort, so sort client-side by parsed price
- Airbnb: `airbnb_listing_details` reveals amenities (wifi, AC, kitchen), house rules, and exact coordinates — crucial for final picks
- Airbnb: pagination returns ~18 results/page, up to ~270 total (15 pages via cursors)
