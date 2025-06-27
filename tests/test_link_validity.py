"""Test link validity checking."""

import asyncio
from obsidianpilot.tools.link_management import get_outgoing_links, find_broken_links

async def test_daily_note_links():
    """Test link validity in today's daily note."""
    
    daily_note_path = "Daily/2025-06-09.md"
    
    print(f"Testing link validity for: {daily_note_path}")
    print("=" * 60)
    
    # Test get_outgoing_links with validity checking
    print("\n1. Testing get_outgoing_links with check_validity=True:")
    try:
        result = await get_outgoing_links(daily_note_path, check_validity=True)
        print(f"   Found {result['link_count']} links:")
        for link in result['links']:
            status = "✓ EXISTS" if link['exists'] else "✗ BROKEN"
            actual = f" (actually at: {link.get('actual_path', '')})" if link.get('actual_path') else ""
            print(f"   - {link['display_text']} -> {link['path']} [{status}]{actual}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test find_broken_links on single note
    print("\n2. Testing find_broken_links on single note:")
    try:
        result = await find_broken_links(single_note=daily_note_path)
        print(f"   Found {result['broken_link_count']} broken links:")
        for link in result['broken_links']:
            print(f"   - {link['link_text']} -> {link['broken_link']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_daily_note_links())