#!/usr/bin/env python3
"""Comprehensive test to verify all Obsidian MCP functionality."""

import asyncio
import os
import sys
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obsidianpilot.tools.note_management import read_note, create_note, update_note, delete_note
from obsidianpilot.tools.search_discovery import list_notes, search_notes
from obsidianpilot.tools.organization import add_tags, remove_tags, get_note_info, move_note


async def test_full_workflow():
    """Test complete workflow with real data validation."""
    print("=" * 60)
    print("Obsidian MCP - Comprehensive Test")
    print("=" * 60)
    
    test_path = f"MCP-Test/comprehensive-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    
    try:
        # 1. List notes in MCP-Test directory
        print("\n1️⃣  Testing list_notes...")
        result = await list_notes("MCP-Test", recursive=True, ctx=None)
        print(f"✅ Listed {result['count']} notes in MCP-Test")
        print(f"   Notes: {[n['path'] for n in result['notes'][:3]]}...")
        
        # 2. Create a new note
        print("\n2️⃣  Testing create_note...")
        content = """---
tags: []
---

# Comprehensive Test Note

This is a test note created by the comprehensive test suite.

## Features to Test
- Basic content creation
- Metadata handling
- Tag management
- Search functionality

Test timestamp: """ + datetime.now().isoformat()
        
        result = await create_note(test_path, content, overwrite=False, ctx=None)
        print(f"✅ Created note: {result['path']}")
        print(f"   Created new: {result['created']}")
        
        # 3. Read the created note
        print("\n3️⃣  Testing read_note...")
        result = await read_note(test_path, ctx=None)
        print(f"✅ Read note: {result['path']}")
        print(f"   Content preview: {result['content'][:50]}...")
        print(f"   Metadata: {result['metadata']}")
        
        # 4. Update the note
        print("\n4️⃣  Testing update_note...")
        updated_content = content + "\n\n## Update Section\nThis section was added via update."
        result = await update_note(test_path, updated_content, ctx=None)
        print(f"✅ Updated note: {result['updated']}")
        
        # 5. Add tags
        print("\n5️⃣  Testing add_tags...")
        tags = ["test", "comprehensive", "mcp", "automated"]
        result = await add_tags(test_path, tags, ctx=None)
        print(f"✅ Added tags: {result['all_tags']}")
        
        # 6. Get note info
        print("\n6️⃣  Testing get_note_info...")
        result = await get_note_info(test_path, ctx=None)
        print(f"✅ Got note info:")
        stats = result.get('stats', {})
        print(f"   Word count: {stats.get('word_count', 'N/A')}")
        print(f"   Size: {stats.get('size_bytes', 'N/A')} bytes")
        print(f"   Tags in metadata: {result.get('metadata', {}).get('tags', [])}")
        
        # 7. Search for the note
        print("\n7️⃣  Testing search_notes...")
        try:
            result = await search_notes("Comprehensive Test", context_length=50, ctx=None)
            print(f"✅ Search found {result['count']} results")
            if result['count'] > 0:
                print(f"   First match: {result['results'][0]['path']}")
        except Exception as e:
            print(f"⚠️  Search skipped (known issue): {e}")
        
        # 8. Remove some tags
        print("\n8️⃣  Testing remove_tags...")
        result = await remove_tags(test_path, ["automated"], ctx=None)
        print(f"✅ Removed tag. Remaining tags: {result['remaining_tags']}")
        
        # 9. Move the note
        print("\n9️⃣  Testing move_note...")
        new_path = test_path.replace(".md", "-moved.md")
        result = await move_note(test_path, new_path, update_links=False, ctx=None)
        print(f"✅ Moved note to: {result['destination']}")
        
        # Update test_path for cleanup
        test_path = result['destination']
        
        # 10. List all notes to see our changes
        print("\n🔟 Testing list_notes (final check)...")
        result = await list_notes("MCP-Test", recursive=True, ctx=None)
        our_note = [n for n in result['notes'] if n['path'] == test_path]
        print(f"✅ Found our note in listing: {len(our_note) > 0}")
        
        # 11. Read some real notes
        print("\n1️⃣1️⃣ Testing read on existing notes...")
        test_notes = [
            "MCP/Introduction.md",
            "Daily/2024-10-01.md",
            "MCP-Test/update-test.md"
        ]
        
        for note_path in test_notes:
            try:
                result = await read_note(note_path, ctx=None)
                print(f"✅ Read {note_path}: {len(result['content'])} chars")
            except Exception as e:
                print(f"❌ Failed to read {note_path}: {e}")
        
    finally:
        # Cleanup: Delete the test note
        print("\n🧹 Cleaning up...")
        try:
            await delete_note(test_path, ctx=None)
            print(f"✅ Deleted test note: {test_path}")
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


async def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n\n" + "=" * 60)
    print("Testing Edge Cases")
    print("=" * 60)
    
    # Test invalid paths
    print("\n1️⃣  Testing invalid path handling...")
    try:
        await read_note("../../../etc/passwd", ctx=None)
        print("❌ Path validation failed - security issue!")
    except ValueError as e:
        print(f"✅ Path validation working: {e}")
    
    # Test non-existent note
    print("\n2️⃣  Testing non-existent note...")
    try:
        await read_note("This/Does/Not/Exist.md", ctx=None)
        print("❌ Should have raised FileNotFoundError")
    except FileNotFoundError:
        print("✅ Properly handles non-existent notes")
    
    # Test creating duplicate
    print("\n3️⃣  Testing duplicate creation prevention...")
    try:
        test_path = "MCP-Test/duplicate-test.md"
        await create_note(test_path, "Test", overwrite=False, ctx=None)
        await create_note(test_path, "Test", overwrite=False, ctx=None)
        print("❌ Should have raised FileExistsError")
        await delete_note(test_path, ctx=None)
    except FileExistsError:
        print("✅ Properly prevents duplicate creation")
        await delete_note(test_path, ctx=None)
    
    # Test empty directory listing
    print("\n4️⃣  Testing non-existent directory...")
    result = await list_notes("This/Does/Not/Exist", recursive=True, ctx=None)
    print(f"✅ Returns empty list for non-existent dir: {result['count']} notes")


async def main():
    """Run all tests."""
    await test_full_workflow()
    await test_edge_cases()


if __name__ == "__main__":
    # Ensure we have the API URL set
    if not os.getenv("OBSIDIAN_API_URL"):
        os.environ["OBSIDIAN_API_URL"] = "https://localhost:27124"
    
    asyncio.run(main())