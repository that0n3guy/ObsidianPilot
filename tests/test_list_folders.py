"""Test the list_folders functionality."""

import asyncio
import os
from obsidianpilot.tools import list_folders

async def test_list_folders():
    """Test listing folders in the vault."""
    print("\n=== Testing list_folders ===")
    
    # Test 1: List all folders recursively
    print("\n1. List all folders recursively:")
    try:
        result = await list_folders(recursive=True)
        print(f"Found {result['count']} folders")
        if result['folders']:
            print("First 5 folders:")
            for folder in result['folders'][:5]:
                print(f"  - {folder['path']} (name: {folder['name']})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: List folders in a specific directory
    print("\n2. List folders in a specific directory (non-recursive):")
    try:
        result = await list_folders(directory="Daily", recursive=False)
        print(f"Found {result['count']} folders in Daily/")
        for folder in result['folders']:
            print(f"  - {folder['path']} (name: {folder['name']})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Test with a non-existent directory
    print("\n3. Test with non-existent directory:")
    try:
        result = await list_folders(directory="NonExistentFolder")
        print(f"Found {result['count']} folders")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure API key is set
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("Error: OBSIDIAN_REST_API_KEY environment variable must be set")
        exit(1)
    
    asyncio.run(test_list_folders())