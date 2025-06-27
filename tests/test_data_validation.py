#!/usr/bin/env python3
"""Test to validate the data returned by each function."""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obsidianpilot.tools.note_management import read_note, create_note, update_note, delete_note
from obsidianpilot.tools.search_discovery import list_notes
from obsidianpilot.tools.organization import add_tags, get_note_info


async def test_return_values():
    """Test and display the return values of each function."""
    print("=" * 60)
    print("Data Validation Test - Return Values")
    print("=" * 60)
    
    test_path = f"MCP-Test/validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    
    try:
        # 1. Test list_notes return value
        print("\n1️⃣  list_notes() return value:")
        result = await list_notes("MCP-Test", recursive=True, ctx=None)
        print(json.dumps(result, indent=2))
        
        # 2. Test create_note return value
        print("\n2️⃣  create_note() return value:")
        content = """---
title: Validation Test
tags: []
---

# Validation Test Note

This note tests return values."""
        
        result = await create_note(test_path, content, overwrite=False, ctx=None)
        print(json.dumps(result, indent=2))
        
        # 3. Test read_note return value
        print("\n3️⃣  read_note() return value:")
        result = await read_note(test_path, ctx=None)
        print(json.dumps({
            "path": result["path"],
            "content": result["content"][:100] + "...",
            "metadata": result["metadata"]
        }, indent=2))
        
        # 4. Test update_note return value
        print("\n4️⃣  update_note() return value:")
        result = await update_note(test_path, content + "\n\nUpdated!", ctx=None)
        print(json.dumps(result, indent=2))
        
        # 5. Test add_tags return value
        print("\n5️⃣  add_tags() return value:")
        result = await add_tags(test_path, ["test", "validation"], ctx=None)
        print(json.dumps(result, indent=2))
        
        # 6. Test get_note_info return value
        print("\n6️⃣  get_note_info() return value:")
        result = await get_note_info(test_path, ctx=None)
        print(json.dumps(result, indent=2))
        
        # 7. Test delete_note return value
        print("\n7️⃣  delete_note() return value:")
        result = await delete_note(test_path, ctx=None)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        # Try to clean up
        try:
            await delete_note(test_path, ctx=None)
        except:
            pass


async def test_real_notes():
    """Test reading real notes to see their structure."""
    print("\n\n" + "=" * 60)
    print("Testing Real Notes")
    print("=" * 60)
    
    # Test a few different directories
    dirs_to_test = ["MCP", "Daily", "Knowledge"]
    
    for dir_name in dirs_to_test:
        print(f"\n📁 Listing {dir_name} directory:")
        try:
            result = await list_notes(dir_name, recursive=False, ctx=None)
            print(f"   Found {result['count']} notes")
            if result['notes']:
                # Try to read the first note
                first_note = result['notes'][0]['path']
                print(f"   Reading first note: {first_note}")
                
                note_data = await read_note(first_note, ctx=None)
                print(f"   - Content length: {len(note_data['content'])} chars")
                print(f"   - Metadata: {note_data['metadata']}")
                
                info = await get_note_info(first_note, ctx=None)
                print(f"   - Stats: {info['stats']}")
        except Exception as e:
            print(f"   Error: {e}")


async def main():
    """Run all tests."""
    await test_return_values()
    await test_real_notes()
    
    print("\n" + "=" * 60)
    print("✅ Data validation complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Ensure we have the API URL set
    if not os.getenv("OBSIDIAN_API_URL"):
        os.environ["OBSIDIAN_API_URL"] = "https://localhost:27124"
    
    asyncio.run(main())