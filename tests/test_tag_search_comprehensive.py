"""Test comprehensive tag search functionality."""

import asyncio
import os
from obsidianpilot.tools import search_notes, list_tags

async def test_tag_search():
    """Test tag search functionality."""
    print("\n=== Testing Tag Search ===")
    
    # Test 1: Search for daily tag
    print("\n1. Searching for 'daily' tag:")
    try:
        result = await search_notes("tag:#daily")
        print(f"Found {result['count']} notes with 'daily' tag")
        if result['results']:
            print("First 5 results:")
            for note in result['results'][:5]:
                print(f"  - {note['path']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Search for J71P tag
    print("\n2. Searching for 'J71P' tag:")
    try:
        result = await search_notes("tag:#J71P")
        print(f"Found {result['count']} notes with 'J71P' tag")
        for note in result['results']:
            print(f"  - {note['path']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: List all tags for reference
    print("\n3. Available tags in vault:")
    try:
        result = await list_tags(include_counts=True, sort_by="count")
        print(f"Total tags: {result['total_tags']}")
        print("Top 10 tags by usage:")
        for tag in result['tags'][:10]:
            print(f"  - {tag['name']}: {tag['count']} uses")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Regular content search (not tag)
    print("\n4. Regular content search for 'Apple':")
    try:
        result = await search_notes("Apple")
        print(f"Found {result['count']} notes containing 'Apple'")
        if result['results']:
            print("First 3 results:")
            for note in result['results'][:3]:
                print(f"  - {note['path']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure API key is set
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("Error: OBSIDIAN_REST_API_KEY environment variable must be set")
        exit(1)
    
    asyncio.run(test_tag_search())