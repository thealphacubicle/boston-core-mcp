#!/usr/bin/env python3
"""Test script specifically for date range filtering functionality."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from servers.boston_opendata_lambda.lambda_server import query_datastore


async def test_date_range_filtering():
    """Test date range filtering with Vision Zero crash data."""
    print("🧪 Testing Date Range Filtering")
    print("=" * 60)
    
    # Vision Zero Crash Records resource ID
    resource_id = "e4bfe397-6bfc-49c5-9367-c879fac7401d"
    
    print(f"\n📊 Resource ID: {resource_id}")
    print(f"   Dataset: Vision Zero Crash Records")
    
    # Test 1: Query without date filter (baseline)
    print(f"\n1️⃣ Baseline Query (no date filter, limit=100)...")
    try:
        result_baseline = await query_datastore(
            resource_id=resource_id,
            sort="dispatch_ts desc",
            limit=100
        )
        
        baseline_count = result_baseline.count("**Record")
        print(f"   ✅ Baseline returned ~{baseline_count} records")
        print(f"   Preview: {result_baseline[:150]}...")
        
    except Exception as e:
        print(f"   ❌ Baseline query failed: {e}")
        return False
    
    # Test 2: Query with date range (May 2025 - data exists up to May 31, 2025)
    print(f"\n2️⃣ Date Range Query (May 2025, limit=1000)...")
    try:
        result_filtered = await query_datastore(
            resource_id=resource_id,
            sort="dispatch_ts desc",
            limit=1000,  # Get more records to filter
            date_range={
                "field": "dispatch_ts",
                "start_date": "2025-05-01",
                "end_date": "2025-05-31"
            }
        )
        
        filtered_count = result_filtered.count("**Record")
        print(f"   ✅ Filtered query returned ~{filtered_count} records")
        print(f"   Preview: {result_filtered[:200]}...")
        
        # Verify filtering worked
        if filtered_count <= baseline_count:
            print(f"   ✅ Filtering appears to work (filtered: {filtered_count} <= baseline: {baseline_count})")
        else:
            print(f"   ⚠️ Warning: Filtered count ({filtered_count}) > baseline ({baseline_count})")
            print(f"   (This might be okay if baseline limit was too small)")
        
        # Check if result contains May dates
        if "2025-05" in result_filtered:
            print(f"   ✅ Result contains May 2025 dates")
        
    except Exception as e:
        print(f"   ❌ Date range query failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Query with only start_date
    print(f"\n3️⃣ Date Range Query (start_date only, from May 1)...")
    try:
        result_start_only = await query_datastore(
            resource_id=resource_id,
            sort="dispatch_ts desc",
            limit=100,
            date_range={
                "field": "dispatch_ts",
                "start_date": "2025-05-01"
            }
        )
        
        start_only_count = result_start_only.count("**Record")
        print(f"   ✅ Start-date-only query returned ~{start_only_count} records")
        
    except Exception as e:
        print(f"   ❌ Start-date-only query failed: {e}")
        return False
    
    # Test 4: Query with only end_date
    print(f"\n4️⃣ Date Range Query (end_date only, up to May 31)...")
    try:
        result_end_only = await query_datastore(
            resource_id=resource_id,
            sort="dispatch_ts desc",
            limit=100,
            date_range={
                "field": "dispatch_ts",
                "end_date": "2025-05-31"
            }
        )
        
        end_only_count = result_end_only.count("**Record")
        print(f"   ✅ End-date-only query returned ~{end_only_count} records")
        
    except Exception as e:
        print(f"   ❌ End-date-only query failed: {e}")
        return False
    
    print(f"\n" + "=" * 60)
    print(f"✅ All date range filtering tests completed!")
    print(f"=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_date_range_filtering())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

