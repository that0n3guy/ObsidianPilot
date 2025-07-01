#!/usr/bin/env python3
"""Manual test script for fast search functionality."""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ.setdefault("OBSIDIAN_VAULT_PATH", "/path/to/your/vault")  # UPDATE THIS
os.environ.setdefault("OBSIDIAN_LOG_LEVEL", "DEBUG")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

from obsidianpilot.utils.filesystem import init_vault
from obsidianpilot.utils.fts_search import get_fts_search, rebuild_fts_index
from obsidianpilot.tools.fast_search import fast_search_notes, get_search_stats


async def test_fast_search():
    """Test the fast search functionality."""
    print("=== Fast Search Test Suite ===\n")
    
    try:
        # Initialize the vault first
        print("0. Initializing vault...")
        vault_path = os.environ.get("OBSIDIAN_VAULT_PATH")
        print(f"   Vault path: {vault_path}")
        
        # Check if vault path exists
        if not os.path.exists(vault_path):
            raise FileNotFoundError(f"Vault path does not exist: {vault_path}")
        
        init_vault()
        print("   ✅ Vault initialized")
        
        # Test 1: Check search stats
        print("\n1. Checking search index status...")
        stats = await get_search_stats()
        print(f"   Status: {stats.get('status')}")
        print(f"   Indexed files: {stats.get('total_indexed_files')}")
        print(f"   Index freshness: {stats.get('index_freshness')}")
        
        # Count actual files in vault
        from obsidianpilot.utils.filesystem import get_vault
        vault = get_vault()
        all_notes = await vault.list_notes(recursive=True)
        print(f"   Total notes in vault: {len(all_notes)}")
        
        # Test 2: Force rebuild to see what happens
        if len(all_notes) > stats.get('total_indexed_files', 0) + 10:  # If more than 10 files difference
            print(f"\n2. Index has {stats.get('total_indexed_files', 0)} files but vault has {len(all_notes)} notes. Rebuilding...")
            rebuild_result = await rebuild_fts_index()
            print(f"   Rebuilt with {rebuild_result} files indexed out of {len(all_notes)} total")
        else:
            print(f"\n2. Index already has {stats['total_indexed_files']} files")
        
        # Test 3: Simple search
        print("\n3. Testing simple search...")
        results = await fast_search_notes("project", max_results=5)
        print(f"   Found {results['total_count']} results for 'project'")
        for i, result in enumerate(results['results'][:2]):
            print(f"   - {result['path']}: {result['context'][:100]}...")
        
        # Test 4: Boolean search
        print("\n4. Testing boolean search...")
        results = await fast_search_notes("project OR task", max_results=5)
        print(f"   Found {results['total_count']} results for 'project OR task'")
        
        # Test 5: Phrase search
        print("\n5. Testing phrase search...")
        results = await fast_search_notes("machine learning", max_results=3)
        print(f"   Found {results['total_count']} results for phrase 'machine learning'")
        
        # Test 6: Performance comparison
        print("\n6. Performance comparison...")
        import time
        
        # Time the fast search
        start = time.time()
        fast_results = await fast_search_notes("python", max_results=10)
        fast_time = time.time() - start
        
        print(f"   Fast search: {fast_time:.3f}s for {fast_results['total_count']} results")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Update the vault path below!
    vault_path = input("Enter your Obsidian vault path (or press Enter to use default): ").strip()
    if vault_path:
        os.environ["OBSIDIAN_VAULT_PATH"] = vault_path
    
    if not os.environ.get("OBSIDIAN_VAULT_PATH") or os.environ["OBSIDIAN_VAULT_PATH"] == "/path/to/your/vault":
        print("❌ Please set OBSIDIAN_VAULT_PATH environment variable or edit this script")
        sys.exit(1)
    
    asyncio.run(test_fast_search())