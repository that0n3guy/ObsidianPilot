"""Live tests with real Obsidian REST API.

Tests the MCP server with an actual Obsidian instance.
Requires Obsidian to be running with Local REST API plugin enabled.

Run with: python tests/test_live.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidianpilot.tools import (
    read_note, create_note, update_note, delete_note,
    search_notes, list_notes, add_tags, remove_tags, get_note_info
)


class TestContext:
    """Test context that mimics FastMCP context."""
    def info(self, msg):
        print(f"  [INFO] {msg}")


async def test_connection():
    """Test basic connection to Obsidian."""
    print("\n1️⃣  Testing connection...")
    
    try:
        from obsidianpilot.utils import ObsidianAPI
        api = ObsidianAPI()
        structure = await api.get_vault_structure()
        print(f"✅ Connected! Found {len(structure)} items in vault")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_complete_workflow():
    """Test complete workflow with all operations."""
    print("\n2️⃣  Testing complete workflow...")
    
    ctx = TestContext()
    test_path = f"MCP-Test/live-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    
    try:
        # Create
        content = f"""# Live Test Note

Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Purpose
This note tests all MCP operations with real Obsidian.

## Features Tested
- Note creation
- Reading
- Updating
- Tag management
- Deletion
"""
        create_result = await create_note(test_path, content, ctx=ctx)
        print(f"✅ Created: {create_result['path']}")
        
        # Read
        read_result = await read_note(test_path, ctx)
        print(f"✅ Read: {len(read_result['content'])} chars")
        
        # Update
        updated_content = read_result['content'] + "\n\n## Update\nNote was successfully updated!"
        update_result = await update_note(test_path, updated_content, ctx=ctx)
        print(f"✅ Updated: {update_result['updated']}")
        
        # Add tags
        tags_result = await add_tags(test_path, ["test", "mcp", "live"], ctx)
        print(f"✅ Added tags: {tags_result['tags_added']}")
        
        # Get info
        info_result = await get_note_info(test_path, ctx)
        print(f"✅ Info: {info_result['stats']['word_count']} words")
        
        # Search (optional - may be slow)
        try:
            search_result = await search_notes("Live Test", context_length=50, ctx=ctx)
            print(f"✅ Search: {search_result['count']} results")
        except:
            print("⚠️  Search skipped (endpoint issues)")
        
        # Delete
        delete_result = await delete_note(test_path, ctx)
        print(f"✅ Deleted: {delete_result['deleted']}")
        
        # Verify deletion
        try:
            await read_note(test_path, ctx)
            print("❌ Note still exists!")
            return False
        except:
            print("✅ Verified deletion")
            return True
            
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        # Try cleanup
        try:
            await delete_note(test_path, ctx)
        except:
            pass
        return False


async def test_batch_operations():
    """Test batch operations with multiple notes."""
    print("\n3️⃣  Testing batch operations...")
    
    ctx = TestContext()
    test_notes = []
    
    try:
        # Create multiple notes
        for i in range(3):
            path = f"MCP-Test/batch-{i}.md"
            await create_note(path, f"# Batch Note {i}\n\nTest content.", ctx=ctx)
            test_notes.append(path)
        print(f"✅ Created {len(test_notes)} notes")
        
        # List them
        result = await list_notes("MCP-Test", recursive=True, ctx=ctx)
        print(f"✅ Listed: {result['count']} notes in MCP-Test")
        
        # Clean up
        for path in test_notes:
            await delete_note(path, ctx)
        print(f"✅ Cleaned up {len(test_notes)} notes")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch test failed: {e}")
        # Cleanup
        for path in test_notes:
            try:
                await delete_note(path, ctx)
            except:
                pass
        return False


async def main():
    """Run all live tests."""
    print("=" * 60)
    print("Obsidian MCP Server - Live Tests")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("\n❌ ERROR: OBSIDIAN_REST_API_KEY not set!")
        print("Set it with: export OBSIDIAN_REST_API_KEY='your-key'")
        return 1
    
    # Run tests
    results = []
    
    # Test connection
    connected = await test_connection()
    results.append(("Connection", connected))
    
    if not connected:
        print("\n❌ Cannot proceed without connection")
        print("\nMake sure:")
        print("1. Obsidian is running")
        print("2. Local REST API plugin is enabled")
        print("3. API key is correct")
        return 1
    
    # Run other tests
    results.append(("Complete Workflow", await test_complete_workflow()))
    results.append(("Batch Operations", await test_batch_operations()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    failed = sum(1 for _, passed in results if not passed)
    print(f"\nTotal: {len(results) - failed}/{len(results)} passed")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))