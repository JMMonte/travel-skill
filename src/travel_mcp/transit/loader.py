"""Load and merge city transit configs from the cities/ directory."""

import json
import os
from pathlib import Path

CITIES_DIR = Path(__file__).parent.parent.parent.parent / "cities"
DATA_DIR = os.environ.get("TRAVEL_MCP_DATA_DIR", "/tmp/gtfs-mcp/data")
SCHEDULE_REFRESH_HOURS = 168  # 1 week


def load_city_configs() -> list[dict]:
    """Load all city JSON configs from the cities/ directory."""
    configs = []
    if not CITIES_DIR.exists():
        return configs

    for f in sorted(CITIES_DIR.glob("*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
                configs.append(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: skipping {f.name}: {e}")
    return configs


def build_gtfs_config() -> dict:
    """Build a merged gtfs-mcp config from all city configs."""
    systems = []
    for city_config in load_city_configs():
        for system in city_config.get("systems", []):
            systems.append(system)

    return {
        "systems": systems,
        "data_dir": DATA_DIR,
        "schedule_refresh_hours": SCHEDULE_REFRESH_HOURS,
    }


def write_merged_config(output_path: str | None = None) -> str:
    """Build and write the merged config to a temp file. Returns the file path."""
    import tempfile

    config = build_gtfs_config()

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".json", prefix="gtfs-config-")
        os.close(fd)

    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)

    return output_path


def list_cities() -> list[dict]:
    """List all configured cities with their system IDs."""
    result = []
    for city_config in load_city_configs():
        city = city_config.get("city", "Unknown")
        country = city_config.get("country", "??")
        system_ids = [s["id"] for s in city_config.get("systems", [])]
        has_realtime = any(
            any(s.get("realtime", {}).get(k) for k in ["trip_updates", "vehicle_positions", "alerts"])
            for s in city_config.get("systems", [])
        )
        result.append({
            "city": city,
            "country": country,
            "systems": system_ids,
            "realtime": has_realtime,
        })
    return result


if __name__ == "__main__":
    # Print merged config for debugging
    print(json.dumps(build_gtfs_config(), indent=2))
    print(f"\n--- {len(build_gtfs_config()['systems'])} systems from {len(load_city_configs())} cities ---")
    for c in list_cities():
        rt = " (realtime)" if c["realtime"] else ""
        print(f"  {c['city']} ({c['country']}): {', '.join(c['systems'])}{rt}")
