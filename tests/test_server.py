import asyncio
import os

import httpx

async def test_obsidian_connection():
    """Test that we can connect to Obsidian's REST API."""
    api_key = os.getenv("OBSIDIAN_REST_API_KEY")
    client = httpx.AsyncClient(
        verify=False,
        headers={"Authorization": f"Bearer {api_key}"}
    )

    try:
        response = await client.get("https://localhost:27124/")
        print(f"Connection successful: {response.json()}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_obsidian_connection())