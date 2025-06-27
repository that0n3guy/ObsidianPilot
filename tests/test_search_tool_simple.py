"""Simple test for search_by_date tool."""

import asyncio
from obsidianpilot.tools import search_by_date

async def main():
    print("Testing search_by_date tool...\n")
    
    # Test 1: Search for notes modified in last 7 days
    print("1. Searching for notes modified in last 7 days:")
    try:
        result = await search_by_date(date_type="modified", days_ago=7, operator="within")
        print(f"   ✅ Found {result['count']} notes")
        print(f"   Query: {result['query']}")
        if result['count'] > 0:
            print(f"   Most recent: {result['results'][0]['path']} ({result['results'][0]['days_ago']} days ago)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. Searching for notes created in last 30 days:")
    try:
        result = await search_by_date(date_type="created", days_ago=30, operator="within")
        print(f"   ✅ Found {result['count']} notes")
        print(f"   Query: {result['query']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3. Searching for notes modified exactly 1 day ago:")
    try:
        result = await search_by_date(date_type="modified", days_ago=1, operator="exactly")
        print(f"   ✅ Found {result['count']} notes")
        print(f"   Query: {result['query']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4. Testing with defaults (modified within 7 days):")
    try:
        result = await search_by_date()
        print(f"   ✅ Found {result['count']} notes")
        print(f"   Query: {result['query']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n5. Searching for notes created this week:")
    try:
        result = await search_by_date(date_type="created", days_ago=7)
        print(f"   ✅ Found {result['count']} notes created this week")
        if result['count'] > 0:
            print("   Recent creations:")
            for note in result['results'][:3]:  # Show first 3
                print(f"     - {note['path']} ({note['days_ago']} days ago)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())