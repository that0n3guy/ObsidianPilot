"""Wrapper for Obsidian REST API interactions."""

import os
import httpx
import urllib3
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from ..constants import OBSIDIAN_BASE_URL, DEFAULT_TIMEOUT, ENDPOINTS, ERROR_MESSAGES
from ..models import Note, NoteMetadata, VaultItem

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ObsidianAPI:
    """Client for interacting with Obsidian REST API."""
    
    # Class-level client for connection pooling
    _client: Optional[httpx.AsyncClient] = None
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Obsidian API client.
        
        Args:
            api_key: API key for authentication. If not provided, reads from environment.
            base_url: Base URL for the API. If not provided, uses default or environment.
        """
        self.api_key = api_key or os.getenv("OBSIDIAN_REST_API_KEY")
        if not self.api_key:
            raise ValueError(ERROR_MESSAGES["api_key_missing"])
        
        # Allow base URL override from environment
        self.base_url = base_url or os.getenv("OBSIDIAN_API_URL", OBSIDIAN_BASE_URL)
        # Ensure base URL doesn't end with a slash
        self.base_url = self.base_url.rstrip('/')
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """Get or create a shared HTTP client with connection pooling."""
        if cls._client is None or cls._client.is_closed:
            # Create client with connection pooling
            # Reduced timeout for local API (was 30 seconds)
            cls._client = httpx.AsyncClient(
                verify=False,
                timeout=httpx.Timeout(10.0),  # 10 second timeout for local API
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                    keepalive_expiry=30.0
                )
            )
        return cls._client
    
    @classmethod
    async def close_client(cls):
        """Close the shared HTTP client."""
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
        
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make an authenticated request to the Obsidian API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body data
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPError: On connection errors
        """
        # Ensure proper URL construction without double slashes
        base_url = self.base_url.rstrip('/')
        endpoint = '/' + endpoint.lstrip('/')
        url = f"{base_url}{endpoint}"
        
        async with httpx.AsyncClient(verify=False, timeout=DEFAULT_TIMEOUT) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json_data
                )
                response.raise_for_status()
                return response
            except httpx.ConnectError:
                raise ConnectionError(
                    ERROR_MESSAGES["connection_failed"].format(
                        url=url, 
                        port=self.base_url.split(":")[-1]
                    )
                )
    
    async def get_vault_structure(self, path: Optional[str] = None) -> List[VaultItem]:
        """Get the vault structure."""
        if path:
            # For directories, we need the trailing slash
            endpoint = f"/vault/{path}/"
        else:
            endpoint = ENDPOINTS["vault"]
        
        response = await self._request("GET", endpoint)
        data = response.json()
        # API returns an object with "files" array when using HTTPS
        items = data.get("files", []) if isinstance(data, dict) else data
        return self._parse_vault_items(items)
    
    async def get_note(self, path: str) -> Optional[Note]:
        """
        Get a note by path.
        
        Args:
            path: Path to the note
            
        Returns:
            Note object or None if not found
        """
        try:
            endpoint = ENDPOINTS["vault_path"].format(path=path)
            # Request JSON format to get tags and metadata
            headers = self.headers.copy()
            headers["Accept"] = "application/vnd.olrapi.note+json"
            
            async with httpx.AsyncClient(verify=False, timeout=DEFAULT_TIMEOUT) as client:
                # Ensure proper URL construction
                base_url = self.base_url.rstrip('/')
                endpoint = '/' + endpoint.lstrip('/')
                url = f"{base_url}{endpoint}"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            
            # Parse JSON response which should include tags
            data = response.json()
            content = data.get("content", "")
            
            # Parse metadata with proper tag handling
            metadata = self._parse_metadata(data)
            
            return Note(
                path=path,
                content=content,
                metadata=metadata
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def create_note(self, path: str, content: str) -> Note:
        """
        Create a new note.
        
        Args:
            path: Path for the new note
            content: Markdown content
            
        Returns:
            Created note
        """
        endpoint = ENDPOINTS["vault_path"].format(path=path)
        
        # Send content as plain text markdown, not JSON
        async with httpx.AsyncClient(verify=False, timeout=DEFAULT_TIMEOUT) as client:
            url = f"{self.base_url}{endpoint}"
            headers = self.headers.copy()
            headers["Content-Type"] = "text/markdown"
            
            response = await client.put(
                url,
                headers=headers,
                content=content  # Send as plain text, not JSON
            )
            response.raise_for_status()
        
        # Try to fetch the created note to get metadata
        # Sometimes Obsidian needs a moment to process large notes
        try:
            import asyncio
            await asyncio.sleep(0.5)  # Small delay to let Obsidian process
            return await self.get_note(path)
        except (httpx.ReadTimeout, httpx.ConnectError):
            # If we can't fetch the note, return a basic Note object
            # The creation was successful (204 response), just can't get fresh metadata
            from datetime import datetime
            return Note(
                path=path,
                content=content,
                metadata=NoteMetadata(
                    created=datetime.now(),
                    modified=datetime.now()
                )
            )
    
    async def update_note(self, path: str, content: str) -> Note:
        """
        Update an existing note.
        
        Args:
            path: Path to the note
            content: New markdown content
            
        Returns:
            Updated note
        """
        endpoint = ENDPOINTS["vault_path"].format(path=path)
        
        # Send content as plain text markdown, not JSON
        async with httpx.AsyncClient(verify=False, timeout=DEFAULT_TIMEOUT) as client:
            url = f"{self.base_url}{endpoint}"
            headers = self.headers.copy()
            headers["Content-Type"] = "text/markdown"
            
            response = await client.put(
                url,
                headers=headers,
                content=content  # Send as plain text, not JSON
            )
            response.raise_for_status()
        
        # Try to fetch the updated note to get fresh metadata
        # Sometimes Obsidian needs a moment to process the update
        try:
            import asyncio
            await asyncio.sleep(0.5)  # Small delay to let Obsidian process
            return await self.get_note(path)
        except (httpx.ReadTimeout, httpx.ConnectError):
            # If we can't fetch the note, return a basic Note object
            # The update was successful (204 response), just can't get fresh metadata
            return Note(
                path=path,
                content=content,
                metadata=NoteMetadata()
            )
    
    async def delete_note(self, path: str) -> bool:
        """
        Delete a note.
        
        Args:
            path: Path to the note
            
        Returns:
            True if deleted successfully
        """
        endpoint = ENDPOINTS["vault_path"].format(path=path)
        try:
            await self._request("DELETE", endpoint)
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for notes.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        # Try multiple search approaches
        
        # 1. Try JsonLogic search (as suggested by Claude)
        try:
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                url = f"{self.base_url}/search"
                headers = self.headers.copy()
                headers["Content-Type"] = "application/vnd.olrapi.jsonlogic+json"
                
                # Check if this is a tag search
                if query.startswith("tag:"):
                    # Extract tag name (remove tag: prefix and optional # prefix)
                    tag_name = query[4:].lstrip("#")
                    
                    # Create JsonLogic query to search in tags array
                    # Tags in the search index don't include the # prefix
                    json_logic_query = {
                        "in": [tag_name, {"var": "tags"}]
                    }
                else:
                    # Regular content/path search
                    json_logic_query = {
                        "or": [
                            # Search in content
                            {"glob": [f"*{query}*", {"var": "content"}]},
                            # Search in filename
                            {"glob": [f"*{query}*", {"var": "path"}]}
                        ]
                    }
                
                response = await client.post(
                    url,
                    headers=headers,
                    json=json_logic_query
                )
                response.raise_for_status()
                
                # Response from JsonLogic search has a different structure
                results = response.json()
                
                # Format results to match expected structure
                formatted_results = []
                
                if isinstance(results, list):
                    for result in results:
                        # Handle different response formats
                        if isinstance(result, str):
                            # Simple string path
                            formatted_results.append({
                                "path": result,
                                "filename": result,
                                "matches": [],
                                "score": 1.0
                            })
                        elif isinstance(result, dict):
                            # Complex result with match info
                            # Extract the actual filename from the result
                            filename = None
                            if "filename" in result and isinstance(result["filename"], dict):
                                filename = result["filename"].get("filename")
                            elif "path" in result and isinstance(result["path"], dict):
                                filename = result["path"].get("filename")
                            elif "filename" in result and isinstance(result["filename"], str):
                                filename = result["filename"]
                            elif "path" in result and isinstance(result["path"], str):
                                filename = result["path"]
                            
                            if filename:
                                formatted_results.append({
                                    "path": filename,
                                    "filename": filename,
                                    "matches": result.get("matches", []),
                                    "score": result.get("score", 1.0)
                                })
                
                return formatted_results
                
        except Exception as e:
            # Log the specific error for debugging
            import sys
            print(f"JsonLogic search failed: {e}", file=sys.stderr)
            
            # 2. Try the simple search endpoint as fallback
            try:
                async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                    url = f"{self.base_url}{ENDPOINTS['search_simple']}"
                    response = await client.post(
                        url,
                        headers=self.headers,
                        json={"query": query, "contextLength": 100}
                    )
                    response.raise_for_status()
                    return response.json()
            except (httpx.TimeoutException, httpx.ConnectError):
                raise ConnectionError("Search endpoints are not available or timed out")
            except httpx.HTTPStatusError as e:
                raise ConnectionError(f"Search failed with status {e.response.status_code}")
    
    async def search_with_jsonlogic(self, json_logic_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search using JsonLogic queries for advanced filtering.
        
        Args:
            json_logic_query: JsonLogic query object
            
        Returns:
            List of search results
        """
        try:
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                url = f"{self.base_url}/search"
                headers = self.headers.copy()
                headers["Content-Type"] = "application/vnd.olrapi.jsonlogic+json"
                
                response = await client.post(
                    url,
                    headers=headers,
                    json=json_logic_query
                )
                response.raise_for_status()
                
                # Response from JsonLogic search has a different structure
                results = response.json()
                
                # Format results to match expected structure
                formatted_results = []
                
                if isinstance(results, list):
                    for result in results:
                        # Handle different response formats
                        if isinstance(result, str):
                            # Simple string path
                            formatted_results.append({
                                "path": result,
                                "filename": result
                            })
                        elif isinstance(result, dict):
                            # Complex result with stat info
                            filename = None
                            if "filename" in result and isinstance(result["filename"], dict):
                                filename = result["filename"].get("filename")
                            elif "path" in result and isinstance(result["path"], dict):
                                filename = result["path"].get("filename")
                            elif "filename" in result and isinstance(result["filename"], str):
                                filename = result["filename"]
                            elif "path" in result and isinstance(result["path"], str):
                                filename = result["path"]
                            
                            if filename:
                                formatted_result = {
                                    "path": filename,
                                    "filename": filename
                                }
                                # Include stat info if available
                                if "stat" in result:
                                    formatted_result["stat"] = result["stat"]
                                formatted_results.append(formatted_result)
                
                return formatted_results
                
        except (httpx.TimeoutException, httpx.ConnectError):
            raise ConnectionError("Search endpoint timed out or is not available")
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Search failed with status {e.response.status_code}")
    
    def _parse_vault_items(self, items: List[str]) -> List[VaultItem]:
        """Parse vault items from API response."""
        result = []
        for item in items:
            # Items ending with / are folders
            is_folder = item.endswith('/')
            clean_path = item.rstrip('/')
            name = clean_path.split('/')[-1] if '/' in clean_path else clean_path
            
            vault_item = VaultItem(
                path=clean_path,
                name=name,
                is_folder=is_folder,
                children=None  # We'll need to fetch children separately for folders
            )
            result.append(vault_item)
        return result
    
    def _parse_metadata(self, data: Dict[str, Any]) -> NoteMetadata:
        """Parse metadata from API response."""
        # Get tags from the API response (includes both frontmatter and inline tags)
        tags = data.get("tags", [])
        
        # Clean tags - remove # prefix if present
        cleaned_tags = [tag.lstrip("#") for tag in tags]
        
        # Get frontmatter data
        frontmatter = data.get("frontmatter", {})
        
        # Get stat data for timestamps
        stat = data.get("stat", {})
        created = None
        modified = None
        
        if stat:
            # Convert milliseconds to seconds for datetime
            if "ctime" in stat:
                created = datetime.fromtimestamp(stat["ctime"] / 1000)
            if "mtime" in stat:
                modified = datetime.fromtimestamp(stat["mtime"] / 1000)
        
        return NoteMetadata(
            tags=cleaned_tags,
            frontmatter=frontmatter,
            created=created,
            modified=modified,
            aliases=frontmatter.get("aliases", [])
        )