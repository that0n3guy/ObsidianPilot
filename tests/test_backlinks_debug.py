"""Debug script for testing backlinks functionality."""

import asyncio
import os
from obsidianpilot.tools.link_management import get_backlinks, extract_links_from_content

# Set the API key from environment
if not os.getenv("OBSIDIAN_REST_API_KEY"):
    print("Please set OBSIDIAN_REST_API_KEY environment variable")
    exit(1)


async def test_backlinks():
    """Test finding backlinks for Apple TOC."""
    from obsidianpilot.utils import ObsidianAPI
    from obsidianpilot.tools.search_discovery import list_notes
    api = ObsidianAPI()
    
    print("Looking for Apple TOC note...")
    try:
        # List all notes and find Apple TOC
        all_notes_result = await list_notes(recursive=True)
        print(f"Found {all_notes_result['count']} total notes in vault")
        
        found_path = None
        for note in all_notes_result['notes']:
            if "Apple TOC" in note['name'] and not "Studies" in note['name']:
                found_path = note['path']
                print(f"Found Apple TOC at: {found_path}")
                break
        
        if not found_path:
            # Let's see what notes contain "Apple" to debug
            apple_notes = [n for n in all_notes_result['notes'] if "Apple" in n['name']]
            print(f"\nFound {len(apple_notes)} notes with 'Apple' in name:")
            for note in apple_notes[:10]:  # Show first 10
                print(f"  - {note['path']}")
            
            if apple_notes:
                # Try the first one that looks like Apple TOC
                for note in apple_notes:
                    if "TOC" in note['name'] and not "Studies" in note['name']:
                        found_path = note['path']
                        print(f"\nUsing: {found_path}")
                        break
            
            if not found_path:
                print("\nCould not find Apple TOC note!")
                return
            
        # First verify we can actually get the note
        print(f"\nVerifying we can access '{found_path}'...")
        # Try different path encodings
        test_paths = [
            found_path,
            found_path.replace(' ', '%20'),  # URL encode spaces
            found_path.replace('/', '%2F'),  # URL encode slashes
        ]
        
        for test_path in test_paths:
            print(f"  Trying: {test_path}")
            try:
                test_note = await api.get_note(test_path)
                if test_note:
                    print(f"    SUCCESS! Content length: {len(test_note.content)} chars")
                    found_path = test_path  # Use the working path
                    break
                else:
                    print(f"    get_note returned None")
            except Exception as e:
                print(f"    Failed: {e}")
        
        # Now test backlinks with the correct path
        print(f"\nTesting backlinks for '{found_path}'...")
        result = await get_backlinks(found_path, include_context=True)
        print(f"\nFound {result['backlink_count']} backlinks")
        
        if result['backlink_count'] > 0:
            print("\nFirst few backlinks:")
            for i, backlink in enumerate(result['backlinks'][:5]):
                print(f"\n{i+1}. Source: {backlink['source_path']}")
                print(f"   Link text: {backlink['link_text']}")
                if 'context' in backlink:
                    print(f"   Context: {backlink['context'][:100]}...")
        else:
            print("\nNo backlinks found - this seems wrong!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_link_extraction():
    """Test link extraction patterns."""
    print("\nTesting link extraction patterns...")
    
    test_content = """
    #daily #J71P
    ###### [[Apple TOC]]
    ##### [[Apple - Studies TOC]]
    ###### [[Apple People Links]]
    
    Some text with [[Images/Apple TOC]] link.
    And another [[Apple TOC|Custom Text]] with alias.
    """
    
    links = extract_links_from_content(test_content)
    print(f"\nExtracted {len(links)} links:")
    for link in links:
        print(f"  - Path: {link['path']}, Display: {link['display_text']}, Type: {link['type']}")


if __name__ == "__main__":
    # Test link extraction first
    test_link_extraction()
    
    # Then test actual backlinks
    asyncio.run(test_backlinks())