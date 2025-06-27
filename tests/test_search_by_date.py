"""Test search_by_date functionality."""

import asyncio
from datetime import datetime, timedelta
from obsidianpilot.tools.search_discovery import search_by_date

async def test_search_by_date():
    """Test the search_by_date function."""
    print("Testing search_by_date functionality...")
    
    # Test 1: Search for notes modified within last 7 days
    try:
        result = await search_by_date(
            date_type="modified",
            days_ago=7,
            operator="within"
        )
        print(f"✅ Test 1 passed: Found {result['count']} notes modified in last 7 days")
        print(f"   Query: {result['query']}")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Search for notes created within last 30 days
    try:
        result = await search_by_date(
            date_type="created",
            days_ago=30,
            operator="within"
        )
        print(f"✅ Test 2 passed: Found {result['count']} notes created in last 30 days")
        print(f"   Query: {result['query']}")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Search for notes modified exactly 1 day ago
    try:
        result = await search_by_date(
            date_type="modified",
            days_ago=1,
            operator="exactly"
        )
        print(f"✅ Test 3 passed: Found {result['count']} notes modified exactly 1 day ago")
        print(f"   Query: {result['query']}")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    # Test 4: Invalid date_type should raise ValueError
    try:
        await search_by_date(
            date_type="invalid",
            days_ago=7
        )
        print("❌ Test 4 failed: Should have raised ValueError for invalid date_type")
    except ValueError as e:
        print(f"✅ Test 4 passed: Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"❌ Test 4 failed with unexpected error: {e}")
    
    # Test 5: Invalid operator should raise ValueError
    try:
        await search_by_date(
            date_type="modified",
            days_ago=7,
            operator="invalid"
        )
        print("❌ Test 5 failed: Should have raised ValueError for invalid operator")
    except ValueError as e:
        print(f"✅ Test 5 passed: Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"❌ Test 5 failed with unexpected error: {e}")
    
    # Test 6: Negative days_ago should raise ValueError
    try:
        await search_by_date(
            date_type="modified",
            days_ago=-5
        )
        print("❌ Test 6 failed: Should have raised ValueError for negative days_ago")
    except ValueError as e:
        print(f"✅ Test 6 passed: Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"❌ Test 6 failed with unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search_by_date())