import sys
from typing import Any, Dict, Optional

import httpx

from .config import CKAN_BASE_URL, API_TIMEOUT


async def ckan_api_call(
    action: str,
    params: Optional[Dict[str, Any]] = None,
    method: str = "GET",
) -> Dict[str, Any]:
    """Make a request to the CKAN API and return the `result` object."""
    url = f"{CKAN_BASE_URL}/{action}"
    if params is None:
        params = {}

    # Log to stderr for debugging (won't interfere with MCP protocol)
    print(f"[DEBUG] Calling CKAN API: {action}", file=sys.stderr)

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        if method == "GET":
            response = await client.get(url, params=params)
        else:
            response = await client.post(url, json=params)

        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            error_msg = data.get("error", {})
            raise ValueError(f"CKAN API Error: {error_msg}")
        return data.get("result", {})

