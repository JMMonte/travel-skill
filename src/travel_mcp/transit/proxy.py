"""Proxy gtfs-mcp Node.js subprocess as a FastMCP server."""

import os
from pathlib import Path

GTFS_MCP_DIR = os.environ.get("GTFS_MCP_DIR", "/tmp/gtfs-mcp")
CONFIG_PATH = str(Path(__file__).parent / "config.travel.json")


def create_transit_proxy():
    """Create a FastMCP proxy to the gtfs-mcp Node.js MCP server.

    Requires gtfs-mcp to be built at GTFS_MCP_DIR (default: /tmp/gtfs-mcp).
    Run scripts/setup-gtfs.sh to install it.
    """
    script_path = os.path.join(GTFS_MCP_DIR, "dist", "index.js")
    if not os.path.exists(script_path):
        raise FileNotFoundError(
            f"gtfs-mcp not found at {script_path}. "
            f"Run: scripts/setup-gtfs.sh"
        )

    from fastmcp.client.transports import NodeStdioTransport
    from fastmcp.server import create_proxy

    transport = NodeStdioTransport(
        script_path=script_path,
        env={**os.environ, "GTFS_MCP_CONFIG": CONFIG_PATH},
    )

    return create_proxy(transport)
