#!/usr/bin/env python
"""Demo script to showcase the merge_strategy functionality.

Run with: python tests/test_merge_strategy_demo.py
"""

import asyncio
import os
from datetime import datetime
from obsidianpilot.tools import create_note, update_note, read_note, delete_note


async def demo_merge_strategies():
    """Demonstrate the different merge strategies for update_note."""
    
    # Test note path
    test_path = f"MCP-Test/merge-strategy-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    
    print("🔧 Merge Strategy Demo")
    print("=" * 50)
    
    try:
        # 1. Create initial note
        print("\n1️⃣  Creating initial note...")
        await create_note(
            test_path,
            """# Merge Strategy Demo

## Initial Content
This is the original content of the note.

### Section 1
Some initial text here.

### Section 2
More initial content."""
        )
        print(f"✅ Created: {test_path}")
        
        # 2. Read initial content
        print("\n2️⃣  Reading initial content...")
        initial = await read_note(test_path)
        print("Initial content:")
        print("-" * 30)
        print(initial["content"])
        print("-" * 30)
        
        # 3. Update with REPLACE strategy (default)
        print("\n3️⃣  Updating with REPLACE strategy (default)...")
        await update_note(
            test_path,
            """# Merge Strategy Demo - REPLACED

## Completely New Content
This content has completely replaced the original.

### New Section
All previous content is gone."""
        )
        
        replaced = await read_note(test_path)
        print("After REPLACE:")
        print("-" * 30)
        print(replaced["content"])
        print("-" * 30)
        
        # 4. Update with APPEND strategy
        print("\n4️⃣  Updating with APPEND strategy...")
        await update_note(
            test_path,
            """## Appended Content
This content was appended to the existing note.

### Additional Section
This demonstrates the append functionality.""",
            merge_strategy="append"
        )
        
        appended = await read_note(test_path)
        print("After APPEND:")
        print("-" * 30)
        print(appended["content"])
        print("-" * 30)
        
        # 5. Another APPEND to show multiple appends
        print("\n5️⃣  Another APPEND operation...")
        await update_note(
            test_path,
            """## Second Append
You can append multiple times!

- Each append adds to the end
- Previous content is preserved
- Two newlines are added between sections""",
            merge_strategy="append"
        )
        
        final = await read_note(test_path)
        print("After second APPEND:")
        print("-" * 30)
        print(final["content"])
        print("-" * 30)
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await delete_note(test_path)
        print("✅ Test note deleted")
        
        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("\nKey takeaways:")
        print("- merge_strategy='replace' (default): Replaces entire content")
        print("- merge_strategy='append': Adds new content to the end")
        print("- Append adds two newlines between old and new content")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        # Try to clean up
        try:
            await delete_note(test_path)
        except:
            pass


async def main():
    """Run the demo."""
    # Check if API key is set
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("⚠️  OBSIDIAN_REST_API_KEY not set")
        print("Set it with: export OBSIDIAN_REST_API_KEY=your-api-key")
        return
    
    await demo_merge_strategies()


if __name__ == "__main__":
    asyncio.run(main())