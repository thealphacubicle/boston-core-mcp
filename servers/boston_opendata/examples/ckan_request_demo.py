"""Example: Quick CKAN requests to Boston Open Data portal (optional).

Requires: `httpx` and optionally `prettyprinter`, `polars`.
Install extras for this example only if desired.
"""

import httpx

try:
    from prettyprinter import pprint
except Exception:  # fallback if prettyprinter is not installed
    from pprint import pprint

BASE_URL = "https://data.boston.gov/api/3/action"
DATASET_ID = "311-service-requests"


async def fetch_dataset_metadata(dataset_id: str):
    url = f"{BASE_URL}/package_show?id={dataset_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def fetch_resource(resource_id: str, limit: int = 5):
    url = f"{BASE_URL}/datastore_search?resource_id={resource_id}&limit={limit}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    import asyncio

    async def main():
        print("Fetching 311 Service Requests dataset metadata...\n")
        metadata = await fetch_dataset_metadata(DATASET_ID)
        print("Dataset Metadata:")
        pprint(metadata)

        print("\n" + "*" * 80 + "\n")
        print("\nFetching sample records from the dataset...\n")
        records = await fetch_resource(
            resource_id="9d7c2214-4709-478a-a2e8-fb2020a5bb94", limit=3
        )
        print("\nSample Records:")
        pprint(records)

    asyncio.run(main())
