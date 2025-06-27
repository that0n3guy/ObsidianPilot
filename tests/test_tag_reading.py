"""Test reading tags from a specific note."""

import asyncio
import os
from obsidianpilot.tools import read_note, get_note_info, search_notes

async def test_tag_reading():
    """Test reading tags from today's daily note."""
    print("\n=== Testing tag reading for 2025-06-09 ===")
    
    # Test 1: Read the note content
    print("\n1. Reading note content:")
    try:
        result = await read_note("Daily/2025-06-09.md")
        print(f"First 200 chars: {result['content'][:200]}...")
        print(f"Tags from metadata: {result['metadata']['tags']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Get note info
    print("\n2. Getting note info:")
    try:
        result = await get_note_info("Daily/2025-06-09.md")
        print(f"Tags: {result['metadata']['tags']}")
        print(f"Created: {result['metadata']['created']}")
        print(f"Modified: {result['metadata']['modified']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Search by tag
    print("\n3. Searching for notes with J71P tag:")
    try:
        result = await search_notes("tag:#J71P")
        print(f"Found {result['count']} notes with J71P tag")
        for note in result['results'][:3]:
            print(f"  - {note['path']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure API key is set
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("Error: OBSIDIAN_REST_API_KEY environment variable must be set")
        exit(1)
    
    asyncio.run(test_tag_reading())