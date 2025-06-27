"""Debug get_note issue."""

import asyncio
from obsidianpilot.utils import ObsidianAPI

async def test_get_note():
    """Test get_note directly."""
    api = ObsidianAPI()
    
    path = "Apple/Apple TOC.md"
    print(f"Testing get_note for: {path}")
    
    try:
        note = await api.get_note(path)
        if note:
            print(f"Success! Note object returned")
            print(f"  Path: {note.path}")
            print(f"  Content length: {len(note.content)}")
            print(f"  Tags: {note.metadata.tags}")
        else:
            print("get_note returned None")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_note())