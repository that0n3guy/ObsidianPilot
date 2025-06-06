"""Wrapper for Obsidian REST API interactions."""

import os
import httpx
import urllib3
from typing import Optional, Dict, Any, List, Union
from ..constants import OBSIDIAN_BASE_URL, DEFAULT_TIMEOUT, ENDPOINTS, ERROR_MESSAGES
from ..models import Note, NoteMetadata, VaultItem

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ObsidianAPI:
    """Client for interacting with Obsidian REST API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Obsidian API client.
        
        Args:
            api_key: API key for authentication. If not provided, reads from environment.
        """
        self.api_key = api_key or os.getenv("OBSIDIAN_REST_API_KEY")
        if not self.api_key:
            raise ValueError(ERROR_MESSAGES["api_key_missing"])
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
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
        url = f"{OBSIDIAN_BASE_URL}{endpoint}"
        
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
                raise ConnectionError(ERROR_MESSAGES["connection_failed"])
    
    async def get_vault_structure(self) -> List[VaultItem]:
        """Get the vault structure."""
        response = await self._request("GET", ENDPOINTS["vault"])
        data = response.json()
        return self._parse_vault_items(data.get("files", []))
    
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
            response = await self._request("GET", endpoint)
            data = response.json()
            
            return Note(
                path=path,
                content=data.get("content", ""),
                metadata=self._parse_metadata(data)
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
        await self._request("PUT", endpoint, json_data={"content": content})
        
        # Fetch the created note to get metadata
        return await self.get_note(path)
    
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
        # Use PUT to replace the entire content
        await self._request("PUT", endpoint, json_data={"content": content})
        
        # Fetch the updated note to get fresh metadata
        return await self.get_note(path)
    
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
        # Use POST for search endpoint
        response = await self._request(
            "POST", 
            ENDPOINTS["search_simple"],
            json_data={"query": query, "contextLength": 100}
        )
        return response.json()
    
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
        return NoteMetadata(
            tags=data.get("tags", []),
            frontmatter=data.get("frontmatter", {})
        )