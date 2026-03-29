"""Proxy gtfs-mcp Node.js subprocess as a FastMCP server.

Automatically merges all city configs from cities/ into a single
gtfs-mcp config file at startup.
"""

import os

GTFS_MCP_DIR = os.environ.get("GTFS_MCP_DIR", "/tmp/gtfs-mcp")


def create_transit_proxy():
    """Create a FastMCP proxy to the gtfs-mcp Node.js MCP server.

    Merges all city configs from cities/*.json into a single config,
    then starts gtfs-mcp as a subprocess.

    Requires gtfs-mcp to be built at GTFS_MCP_DIR (default: /tmp/gtfs-mcp).
    Run scripts/setup-gtfs.sh to install it.
    """
    script_path = os.path.join(GTFS_MCP_DIR, "dist", "index.js")
    if not os.path.exists(script_path):
        raise FileNotFoundError(
            f"gtfs-mcp not found at {script_path}. "
            f"Run: scripts/setup-gtfs.sh"
        )

    # Build merged config from cities/ directory
    from travel_mcp.transit.loader import write_merged_config
    config_path = write_merged_config()

    from fastmcp.client.transports import NodeStdioTransport
    from fastmcp.server import create_proxy

    transport = NodeStdioTransport(
        script_path=script_path,
        env={**os.environ, "GTFS_MCP_CONFIG": config_path},
    )

    return create_proxy(transport)
