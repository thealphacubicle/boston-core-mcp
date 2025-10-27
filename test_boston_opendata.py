#!/usr/bin/env python3
"""Test runner for the Boston OpenData MCP server."""

import asyncio
import sys
from pathlib import Path

# Add the servers directory to the path
sys.path.insert(0, str(Path(__file__).parent / "servers"))

from boston_opendata.tests.test_production_server import main

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test runner crashed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
