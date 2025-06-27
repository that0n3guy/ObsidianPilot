#!/usr/bin/env python3
"""Test the list_notes function to diagnose why it's not finding notes."""

import asyncio
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obsidianpilot.utils.obsidian_api import ObsidianAPI
from obsidianpilot.tools.search_discovery import list_notes

async def test_api_directly():
    """Test the API directly."""
    print("Testing Obsidian API directly...")
    api = ObsidianAPI()
    
    # Test vault root
    print("\n1. Getting vault structure (root):")
    try:
        items = await api.get_vault_structure()
        print(f"   Found {len(items)} items in vault root")
        # Show first few items
        for i, item in enumerate(items[:5]):
            print(f"   - {item.path} {'(folder)' if item.is_folder else ''}")
        if len(items) > 5:
            print(f"   ... and {len(items) - 5} more")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test specific directory
    print("\n2. Getting vault structure for 'MCP' directory:")
    try:
        items = await api.get_vault_structure("MCP")
        print(f"   Found {len(items)} items in MCP directory")
        for item in items[:10]:
            print(f"   - {item.path} {'(folder)' if item.is_folder else ''}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test with lowercase
    print("\n3. Getting vault structure for 'mcp' directory (lowercase):")
    try:
        items = await api.get_vault_structure("mcp")
        print(f"   Found {len(items)} items")
    except Exception as e:
        print(f"   Error: {e}")

async def test_list_notes_tool():
    """Test the list_notes tool function."""
    print("\n\nTesting list_notes tool function...")
    
    # Test root directory
    print("\n1. list_notes() - root directory:")
    try:
        result = await list_notes(directory=None, recursive=True, ctx=None)
        print(f"   Found {result['count']} notes")
        if result['notes']:
            for note in result['notes'][:5]:
                print(f"   - {note}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test MCP directory
    print("\n2. list_notes(directory='MCP'):")
    try:
        result = await list_notes(directory="MCP", recursive=True, ctx=None)
        print(f"   Found {result['count']} notes")
        if result['notes']:
            for note in result['notes'][:5]:
                print(f"   - {note}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test case sensitivity
    print("\n3. list_notes(directory='mcp') - lowercase:")
    try:
        result = await list_notes(directory="mcp", recursive=True, ctx=None)
        print(f"   Found {result['count']} notes")
    except Exception as e:
        print(f"   Error: {e}")

async def test_raw_api_call():
    """Test raw API call to see what's returned."""
    print("\n\nTesting raw API call...")
    import httpx
    
    base_url = os.getenv("OBSIDIAN_API_URL", "http://localhost:27123")
    api_key = os.getenv("OBSIDIAN_REST_API_KEY")
    
    async with httpx.AsyncClient(verify=False) as client:
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Test vault endpoint
        print("\n1. Raw call to /vault/:")
        response = await client.get(f"{base_url}/vault/", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response type: {type(response.json())}")
        data = response.json()
        if isinstance(data, list):
            print(f"   Items: {len(data)}")
            print("   First 5 items:")
            for item in data[:5]:
                print(f"   - {item}")
        
        # Test MCP directory
        print("\n2. Raw call to /vault/MCP:")
        response = await client.get(f"{base_url}/vault/MCP", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Items: {len(data)}")

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Diagnosing list_notes issue")
    print("=" * 60)
    
    print(f"OBSIDIAN_REST_API_KEY: {'Set' if os.getenv('OBSIDIAN_REST_API_KEY') else 'Not set'}")
    print(f"OBSIDIAN_API_URL: {os.getenv('OBSIDIAN_API_URL', 'http://localhost:27123 (default)')}")
    
    await test_raw_api_call()
    await test_api_directly()
    await test_list_notes_tool()

if __name__ == "__main__":
    asyncio.run(main())