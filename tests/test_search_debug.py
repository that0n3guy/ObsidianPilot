"""Debug search functionality."""

import asyncio
import os
import httpx
import json

async def test_search_debug():
    """Debug search functionality."""
    print("\n=== Debugging Search ===")
    
    api_key = os.getenv("OBSIDIAN_REST_API_KEY")
    base_url = os.getenv("OBSIDIAN_API_URL", "https://localhost:27124")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/vnd.olrapi.jsonlogic+json"
    }
    
    # Test 1: Search for notes with J71P tag
    print("\n1. Testing JsonLogic search for J71P tag:")
    json_logic_query = {
        "some": [
            {"var": "tags"},
            {"==": [{"var": ""}, "J71P"]}
        ]
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{base_url}/search/"
            response = await client.post(
                url,
                headers=headers,
                json=json_logic_query
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Results: {len(data) if isinstance(data, list) else data}")
            if data:
                print("First result:", json.dumps(data[0] if isinstance(data, list) else data, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Try Dataview DQL search
    print("\n2. Testing Dataview DQL search for #J71P:")
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{base_url}/search/"
            
            dql_query = 'TABLE file.name FROM #J71P'
            
            headers_dql = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/vnd.olrapi.dataview.dql+txt"
            }
            
            response = await client.post(
                url,
                headers=headers_dql,
                content=dql_query
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Results: {json.dumps(data, indent=2)}")
            else:
                print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Try different JsonLogic approach
    print("\n3. Testing JsonLogic with in operator for tags:")
    
    json_logic_query = {
        "in": ["J71P", {"var": "tags"}]
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{base_url}/search/"
            response = await client.post(
                url,
                headers=headers,
                json=json_logic_query
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Results: {len(data) if isinstance(data, list) else data}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search_debug())