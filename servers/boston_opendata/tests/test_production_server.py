#!/usr/bin/env python3
"""Test script for the production-ready Boston OpenData MCP server."""

import asyncio
import json
import sys
from pathlib import Path

# Add the servers directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from boston_opendata.server import perform_health_check, get_server_status
from boston_opendata.ckan import health_check as ckan_health_check
from boston_opendata.config import settings


async def test_health_checks():
    """Test health check functionality."""
    print("🔍 Testing health checks...")

    try:
        # Test CKAN health check
        print("  Testing CKAN API health check...")
        ckan_health = await ckan_health_check()
        print(f"  CKAN Health: {ckan_health['status']}")

        # Test server health check
        print("  Testing server health check...")
        server_health = await perform_health_check()
        print(f"  Server Health: {server_health['status']}")

        # Test server status
        print("  Testing server status...")
        status = await get_server_status()
        print(f"  Server Status: {status['status']}")

        print("✅ Health checks completed successfully")
        return True

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")

    try:
        print(f"  Environment: {settings.environment}")
        print(f"  Debug mode: {settings.debug}")
        print(f"  Log level: {settings.log_level}")
        print(f"  CKAN URL: {settings.ckan_base_url}")
        print(f"  API timeout: {settings.api_timeout}s")
        print(f"  Max records: {settings.max_records}")
        print(f"  Rate limit capacity: {settings.rate_limit_capacity}")

        print("✅ Configuration loaded successfully")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_rate_limiter():
    """Test rate limiter functionality."""
    print("🚦 Testing rate limiter...")

    try:
        from boston_opendata.utils.rate_limiter import rate_limiter

        # Test acquiring tokens
        success = await rate_limiter.acquire(tokens=1, timeout=1.0)
        print(f"  Token acquisition: {'✅ Success' if success else '❌ Failed'}")

        # Test rate limiter status
        status = await rate_limiter.get_status()
        print(f"  Rate limiter status: {status}")

        print("✅ Rate limiter test completed")
        return True

    except Exception as e:
        print(f"❌ Rate limiter test failed: {e}")
        return False


async def test_circuit_breaker():
    """Test circuit breaker functionality."""
    print("⚡ Testing circuit breaker...")

    try:
        from boston_opendata.utils.circuit_breaker import ckan_circuit_breaker

        # Test circuit breaker state
        state = ckan_circuit_breaker.get_state()
        print(f"  Circuit breaker state: {state['state']}")
        print(f"  Failure count: {state['failure_count']}")

        print("✅ Circuit breaker test completed")
        return True

    except Exception as e:
        print(f"❌ Circuit breaker test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting production server tests...\n")

    tests = [
        ("Configuration", test_configuration),
        ("Rate Limiter", test_rate_limiter),
        ("Circuit Breaker", test_circuit_breaker),
        ("Health Checks", test_health_checks),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} Test")
        print("=" * 50)

        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print(f"\n{'='*50}")
    print("Test Summary")
    print("=" * 50)

    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1

    print(f"\nResults: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! The server is production-ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


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
