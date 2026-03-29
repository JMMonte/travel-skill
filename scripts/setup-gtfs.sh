#!/bin/bash
# Setup gtfs-mcp for transit functionality
# Run once: ./scripts/setup-gtfs.sh

set -e

GTFS_MCP_DIR="${GTFS_MCP_DIR:-$HOME/Development/gtfs-mcp}"

echo "Setting up gtfs-mcp at $GTFS_MCP_DIR..."

if [ ! -d "$GTFS_MCP_DIR" ]; then
    git clone https://github.com/jdamcd/gtfs-mcp.git "$GTFS_MCP_DIR"
fi

cd "$GTFS_MCP_DIR"
npm install
npm run build

echo "gtfs-mcp ready at $GTFS_MCP_DIR"
echo ""
echo "Pre-configured systems (Barcelona Bus, Rome ATAC) will download"
echo "GTFS data on first use (~50MB for Rome)."
echo ""
echo "To install Playwright browsers for hotel search:"
echo "  playwright install chromium"
