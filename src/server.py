import os
import httpx
from fastmcp import FastMCP
from typing import Optional, Dict, Any
import urllib3

# Suppress SSL warnings for self-signed certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

mcp = FastMCP("obsidian-mcp")

OBSIDIAN_API_URL = "https://localhost:27124"
OBSIDIAN_API_KEY = os.getenv("OBSIDIAN_REST_API_KEY")

# Create reusable client with proper configuration
client = httpx.AsyncClient(
    verify=False,
    headers={"Authorization": f"Bearer {OBSIDIAN_API_KEY}"},
    timeout=30.0,
    base_url=OBSIDIAN_API_URL
)

@mcp.tool()
async def read_note(path: str) -> Dict[str, Any]:
    """Read the content of a specific note by its path."""
    try:
        response = await client.get(f"/vault/{path}")
        response.raise_for_status()

        return {
            "success": True,
            "path": path,
            "content": response.text
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"Note not found: {path}"
            }
        return {
            "success": False,
            "error": f"Failed to read note: {str(e)}"
        }

@mcp.tool()
async def create_note(path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    """Create a new note or update an existing one."""
    try:
        # Check if file exists
        existing_response = await client.get(f"/vault/{path}")
        exists = existing_response.status_code == 200

        if exists and not overwrite:
            return {
                "success": False,
                "error": f"Note already exists: {path}. Set overwrite=True to replace."
            }

        # Create or update the note
        response = await client.put(
            f"/vault/{path}",
            content=content,
            headers={"Content-Type": "text/markdown"}
        )
        response.raise_for_status()

        return {
            "success": True,
            "path": path,
            "action": "updated" if exists else "created",
            "message": f"Successfully {'updated' if exists else 'created'} note at {path}"
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"Failed to create note: {str(e)}"
        }

@mcp.tool()
async def search_notes(query: str, context_length: int = 100) -> Dict[str, Any]:
    """Search for notes containing the specified query."""
    try:
        response = await client.post(
            "/search/simple/",
            params={
                "query": query,
                "contextLength": context_length
            }
        )
        response.raise_for_status()

        results = response.json()
        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }

@mcp.tool()
async def list_notes(directory: Optional[str] = None, recursive: bool = True) -> Dict[str, Any]:
    """
    List notes in the vault.

    Args:
        directory: Specific directory to list (None for root)
        recursive: If True, list all notes recursively. If False, only list the specified directory.
    """
    try:
        if recursive and directory is None:
            # Get all markdown files in the entire vault
            all_notes = []
            errors = []
            await _list_notes_recursive(client, "", all_notes, errors)

            result = {
                "success": True,
                "recursive": True,
                "count": len(all_notes),
                "notes": sorted(all_notes)  # Sort for consistent output
            }

            if errors:
                result["warnings"] = errors

            return result
        else:
            # List only the specified directory
            # Ensure proper formatting of the path
            if directory:
                # Remove leading/trailing slashes and add proper trailing slash
                directory = directory.strip('/')
                endpoint = f"/vault/{directory}/"
            else:
                endpoint = "/vault/"

            response = await client.get(endpoint)
            response.raise_for_status()

            files = response.json().get("files", [])

            # Separate files and folders
            notes = [f for f in files if f.endswith('.md')]
            folders = [f for f in files if f.endswith('/')]

            return {
                "success": True,
                "directory": directory or "root",
                "recursive": False,
                "count": len(notes),
                "notes": notes,
                "folders": folders
            }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"Failed to list notes: {str(e)}"
        }

async def _list_notes_recursive(client: httpx.AsyncClient, path: str, all_notes: list, errors: list):
    """Helper function to recursively list all notes."""
    # Ensure proper path formatting
    if path:
        path = path.strip('/')
        endpoint = f"/vault/{path}/"
    else:
        endpoint = "/vault/"

    try:
        response = await client.get(endpoint)
        response.raise_for_status()

        files = response.json().get("files", [])

        for file in files:
            if file.endswith('.md'):
                # Add the full path
                full_path = f"{path}/{file}" if path else file
                all_notes.append(full_path)
            elif file.endswith('/'):
                # It's a folder, recurse into it
                folder_name = file.rstrip('/')
                folder_path = f"{path}/{folder_name}" if path else folder_name
                await _list_notes_recursive(client, folder_path, all_notes, errors)

    except httpx.HTTPStatusError as e:
        # Record error but continue with other directories
        error_msg = f"Could not access {path or 'root'}: {e.response.status_code}"
        errors.append(error_msg)
    except Exception as e:
        # Catch any other errors
        error_msg = f"Error accessing {path or 'root'}: {str(e)}"
        errors.append(error_msg)

if __name__ == "__main__":
    mcp.run()