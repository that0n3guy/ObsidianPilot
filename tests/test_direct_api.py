"""Test direct API access."""

import os
import httpx
import asyncio
from urllib.parse import quote

async def test_direct_access():
    """Test direct API access to Apple TOC."""
    api_key = os.getenv("OBSIDIAN_REST_API_KEY")
    base_url = "http://localhost:27123"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.olrapi.note+json"
    }
    
    # Test different path formats
    paths = [
        "Apple/Apple TOC.md",
        quote("Apple/Apple TOC.md"),  # URL encode whole path
        f"Apple/{quote('Apple TOC.md')}",  # URL encode just filename
        "Apple/Apple%20TOC.md",  # Manual space encoding
    ]
    
    print("Testing direct API access to Apple TOC...")
    for path in paths:
        url = f"{base_url}/vault/{path}"
        print(f"\nTrying URL: {url}")
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    content_length = len(data.get("content", ""))
                    print(f"  SUCCESS! Content length: {content_length}")
                    print(f"  Path format that works: {path}")
                    return path
                    
        except Exception as e:
            print(f"  Failed: {e}")
    
    return None

if __name__ == "__main__":
    working_path = asyncio.run(test_direct_access())
    if working_path:
        print(f"\nWorking path format: {working_path}")
    else:
        print("\nNo working path format found!")