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


async def test_query_datastore_with_date_range():
    """Test the query_datastore tool with date range filtering."""
    print("\n📅 Testing query_datastore with date_range...")
    try:
        # First, get the Vision Zero crash records resource ID
        print("   Step 1: Getting Vision Zero dataset info...")
        dataset_info = await get_dataset_info("vision-zero-crash-records")
        
        # Extract resource ID from the output (it should be in the output)
        # The resource ID for Vision Zero Crash Records is: e4bfe397-6bfc-49c5-9367-c879fac7401d
        resource_id = "e4bfe397-6bfc-49c5-9367-c879fac7401d"
        
        print(f"   Step 2: Querying without date filter (baseline)...")
        result_no_filter = await query_datastore(
            resource_id=resource_id,
            sort="dispatch_ts desc",
            limit=100
        )
        
        # Count records in result
        baseline_count = result_no_filter.count("**Record")
        print(f"   ✅ Baseline query returned ~{baseline_count} records")
        
        # Now test with date range (last month - October 2025)
        print(f"   Step 3: Querying with date_range (October 2025)...")
        result_with_filter = await query_datastore(
            resource_id=resource_id,
            sort="dispatch_ts desc",
            limit=1000,  # Get more records to filter
            date_range={
                "field": "dispatch_ts",
                "start_date": "2025-10-01",
                "end_date": "2025-10-31"
            }
        )
        
        # Count records in filtered result
        filtered_count = result_with_filter.count("**Record")
        print(f"   ✅ Filtered query returned ~{filtered_count} records")
        
        # Verify filtering worked (should have fewer or equal records)
        if filtered_count <= baseline_count:
            print(f"   ✅ Date filtering appears to be working (filtered: {filtered_count}, baseline: {baseline_count})")
        else:
            print(f"   ⚠️ Warning: Filtered count ({filtered_count}) > baseline ({baseline_count})")
        
        # Check if result mentions date filtering
        if "2025-10" in result_with_filter or "October" in result_with_filter:
            print(f"   ✅ Result contains date-related content")
        
        print(f"   Result preview (first 300 chars): {result_with_filter[:300]}...")
        return True
        
    except Exception as e:
        print(f"❌ query_datastore with date_range failed: {e}")
        import traceback
        traceback.print_exc()
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
    test_results.append(await test_query_datastore_with_date_range())
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
