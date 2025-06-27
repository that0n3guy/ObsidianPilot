"""Test the list_tags functionality."""

import asyncio
import os
from obsidianpilot.tools import list_tags

async def test_list_tags():
    """Test listing all tags in the vault."""
    print("\n=== Testing list_tags ===")
    
    # Test 1: List tags with counts, sorted by name
    print("\n1. List tags with counts (sorted by name):")
    try:
        result = await list_tags(include_counts=True, sort_by="name")
        print(f"Found {result['total_tags']} unique tags")
        if result['tags']:
            print("First 10 tags:")
            for tag in result['tags'][:10]:
                print(f"  - {tag['name']}: {tag['count']} uses")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: List tags sorted by count (most used first)
    print("\n2. List tags sorted by usage count:")
    try:
        result = await list_tags(include_counts=True, sort_by="count")
        if result['tags']:
            print("Top 5 most used tags:")
            for tag in result['tags'][:5]:
                print(f"  - {tag['name']}: {tag['count']} uses")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: List tags without counts
    print("\n3. List tags without counts:")
    try:
        result = await list_tags(include_counts=False)
        print(f"Found {result['total_tags']} unique tags")
        if result['tags']:
            print(f"Sample tags: {result['tags'][:5]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure API key is set
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("Error: OBSIDIAN_REST_API_KEY environment variable must be set")
        exit(1)
    
    asyncio.run(test_list_tags())