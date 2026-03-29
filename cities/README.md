# City Transit Feeds

Each JSON file in this directory defines GTFS transit feeds for a city. The files are automatically merged into the transit server config at startup.

## How to Add a City

1. Create a new file: `cities/<city-name>.json`
2. Follow this template:

```json
{
  "city": "City Name",
  "country": "XX",
  "systems": [
    {
      "id": "city-metro",
      "name": "City Metro",
      "schedule_url": "https://example.com/gtfs.zip",
      "realtime": {
        "trip_updates": [],
        "vehicle_positions": ["https://example.com/vehicles.pb"],
        "alerts": ["https://example.com/alerts.pb"]
      },
      "auth": null
    }
  ]
}
```

3. Test it: `PYTHONPATH=src python3 -c "from travel_mcp.transit.loader import load_config; print(load_config())"`
4. Submit a PR!

## Fields

| Field | Description |
|-------|-------------|
| `city` | Human-readable city name |
| `country` | ISO 3166-1 alpha-2 country code |
| `systems[].id` | Unique ID used in tool calls (e.g., `lisbon-carris`) |
| `systems[].name` | Human-readable system name |
| `systems[].schedule_url` | URL to GTFS static `.zip` file |
| `systems[].realtime.trip_updates` | GTFS-RT trip updates protobuf URLs (can be empty `[]`) |
| `systems[].realtime.vehicle_positions` | GTFS-RT vehicle positions protobuf URLs |
| `systems[].realtime.alerts` | GTFS-RT service alerts protobuf URLs |
| `systems[].auth` | Auth config or `null` (see below) |

## Authentication

For feeds requiring API keys:

```json
"auth": {
  "type": "query_param",
  "param_name": "api_key",
  "key_env": "MY_CITY_API_KEY"
}
```

Or header-based:

```json
"auth": {
  "type": "header",
  "header_name": "X-Api-Key",
  "key_env": "MY_CITY_API_KEY"
}
```

Set the environment variable (e.g., `MY_CITY_API_KEY=abc123`) before starting the server.

## Finding GTFS Feeds

- [Mobility Database](https://mobilitydatabase.org/) — 6000+ feeds worldwide
- [Transitland](https://www.transit.land/) — aggregated feed directory
- City open data portals (search for "GTFS" + city name)

## Data Notes

- Static GTFS data downloads on first query per system (~5-90MB depending on city)
- Data is cached in SQLite and refreshes weekly
- Realtime feeds are fetched on-demand with 30s caching
- Not all cities have realtime feeds — static schedules still work
