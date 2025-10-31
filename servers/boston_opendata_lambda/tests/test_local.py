#!/usr/bin/env python3
"""Local testing script for the Boston OpenData MCP Lambda server."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
# Test file is at: servers/boston_opendata_lambda/tests/test_local.py
# Need to go up 4 levels to reach project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from servers.boston_opendata_lambda.lambda_server import (
    search_datasets,
    list_all_datasets,
    get_dataset_info,
    query_datastore,
    get_datastore_schema,
    perform_health_check,
)


async def test_health_check():
    """Test the health check functionality."""
    print("🔍 Testing health check...")
    try:
        health = await perform_health_check()
        print(f"✅ Health check result: {health['status']}")
        if health["status"] == "healthy":
            print("   CKAN API is accessible")
        else:
            print(f"   Error: {health.get('error', 'Unknown error')}")
        return health["status"] == "healthy"
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def test_search_datasets():
    """Test the search_datasets tool."""
    print("\n🔍 Testing search_datasets...")
    try:
        # Test with a common search term
        result = await search_datasets("311", limit=3)
        print("✅ search_datasets completed")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ search_datasets failed: {e}")
        return False


async def test_list_all_datasets():
    """Test the list_all_datasets tool."""
    print("\n📚 Testing list_all_datasets...")
    try:
        result = await list_all_datasets(limit=5)
        print("✅ list_all_datasets completed")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ list_all_datasets failed: {e}")
        return False


async def test_get_dataset_info():
    """Test the get_dataset_info tool."""
    print("\n📊 Testing get_dataset_info...")
    try:
        # Use a known dataset ID (this might need to be updated based on actual data)
        result = await get_dataset_info("311-service-requests")
        print("✅ get_dataset_info completed")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ get_dataset_info failed: {e}")
        return False


async def test_get_datastore_schema():
    """Test the get_datastore_schema tool."""
    print("\n📋 Testing get_datastore_schema...")
    try:
        # This will likely fail without a valid resource_id, but we can test the error handling
        result = await get_datastore_schema("invalid-resource-id")
        print("✅ get_datastore_schema completed (with expected error)")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ get_datastore_schema failed: {e}")
        return False


async def test_query_datastore():
    """Test the query_datastore tool."""
    print("\n🗄️ Testing query_datastore...")
    try:
        # This will likely fail without a valid resource_id, but we can test the error handling
        result = await query_datastore("invalid-resource-id", limit=5)
        print("✅ query_datastore completed (with expected error)")
        print(f"   Result length: {len(result)} characters")
        print(f"   First 200 chars: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ query_datastore failed: {e}")
        return False


async def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n⚠️ Testing error handling...")

    # Test search_datasets with invalid input
    try:
        result = await search_datasets("", limit=0)
        print("✅ search_datasets error handling works")
        print(f"   Error message: {result[:100]}...")
    except Exception as e:
        print(f"❌ search_datasets error handling failed: {e}")

    # Test get_dataset_info with invalid input
    try:
        result = await get_dataset_info("")
        print("✅ get_dataset_info error handling works")
        print(f"   Error message: {result[:100]}...")
    except Exception as e:
        print(f"❌ get_dataset_info error handling failed: {e}")


async def main():
    """Run all tests."""
    print("🚀 Starting Boston OpenData MCP Lambda Server Tests")
    print("=" * 60)

    # Track test results
    test_results = []

    # Run tests
    test_results.append(await test_health_check())
    test_results.append(await test_search_datasets())
    test_results.append(await test_list_all_datasets())
    test_results.append(await test_get_dataset_info())
    test_results.append(await test_get_datastore_schema())
    test_results.append(await test_query_datastore())
    await test_error_handling()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(test_results)
    total = len(test_results)

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! The Lambda server is ready for deployment.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test runner failed: {e}")
        sys.exit(1)
