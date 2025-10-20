#!/usr/bin/env python3
"""Entry point for running the Census Bureau MCP server over stdio."""

from __future__ import annotations

import asyncio
import sys

from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from .server import app


async def main() -> None:
    print("[INFO] Starting Census Bureau MCP server...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="census-bureau-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Census server stopped by user", file=sys.stderr)
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[ERROR] Census server crashed: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
