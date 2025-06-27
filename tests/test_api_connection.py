"""Test basic API connection."""

import os
import httpx
import asyncio

async def test_connection():
    """Test connection to Obsidian API."""
    api_key = os.getenv("OBSIDIAN_REST_API_KEY")
    if not api_key:
        print("OBSIDIAN_REST_API_KEY not set!")
        return
        
    # Test both possible URLs
    urls = [
        "https://localhost:27124",
        "http://localhost:27124", 
        "https://localhost:27123",
        "http://localhost:27123",
        "http://127.0.0.1:27123",
        "http://127.0.0.1:27124"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    for url in urls:
        print(f"\nTrying {url}...")
        try:
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                response = await client.get(f"{url}/vault/", headers=headers)
                print(f"  Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"  SUCCESS! Use this URL: {url}")
                    # Try to get some data
                    data = response.json()
                    if isinstance(data, dict) and "files" in data:
                        print(f"  Found {len(data['files'])} items in vault root")
                    elif isinstance(data, list):
                        print(f"  Found {len(data)} items in vault root")
                    break
        except Exception as e:
            print(f"  Failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())