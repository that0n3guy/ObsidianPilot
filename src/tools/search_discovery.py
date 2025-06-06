"""Search and discovery tools for Obsidian MCP server."""

from typing import List, Optional
from fastmcp import Context
from ..utils import ObsidianAPI, is_markdown_file
from ..models import SearchResult, VaultItem
from ..constants import DEFAULT_SEARCH_CONTEXT_LENGTH, DEFAULT_LIST_RECURSIVE


async def search_notes(
    query: str,
    context_length: int = DEFAULT_SEARCH_CONTEXT_LENGTH,
    ctx: Context = None
) -> dict:
    """
    Search for notes containing specific text or matching search criteria.
    
    Use this tool to find notes in your vault that match a search query.
    Supports Obsidian's search syntax including tags, phrases, and operators.
    
    Args:
        query: Search query (supports Obsidian search syntax)
        context_length: Number of characters to show around matches (default: 100)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing search results with matched notes and context
        
    Example:
        >>> await search_notes("tag:#project AND Machine Learning", ctx=ctx)
        {
            "query": "tag:#project AND Machine Learning",
            "count": 3,
            "results": [
                {
                    "path": "Projects/ML Pipeline.md",
                    "score": 0.95,
                    "matches": ["implementing machine learning models"],
                    "context": "...focused on implementing machine learning models for production..."
                }
            ]
        }
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if ctx:
        ctx.info(f"Searching notes with query: {query}")
    
    api = ObsidianAPI()
    results = await api.search(query)
    
    # Format results
    formatted_results = []
    for result in results:
        # Extract context around matches
        content = result.get("content", "")
        matches = result.get("matches", [])
        
        # Create context snippets
        contexts = []
        for match in matches[:3]:  # Limit to first 3 matches
            start = max(0, match.get("start", 0) - context_length // 2)
            end = min(len(content), match.get("end", 0) + context_length // 2)
            context = content[start:end].strip()
            if start > 0:
                context = "..." + context
            if end < len(content):
                context = context + "..."
            contexts.append(context)
        
        formatted_results.append({
            "path": result["path"],
            "score": result.get("score", 0.0),
            "matches": [m.get("match", "") for m in matches[:3]],
            "context": " | ".join(contexts) if contexts else ""
        })
    
    return {
        "query": query,
        "count": len(formatted_results),
        "results": formatted_results
    }


async def list_notes(
    directory: Optional[str] = None,
    recursive: bool = DEFAULT_LIST_RECURSIVE,
    ctx: Context = None
) -> dict:
    """
    List notes in the vault or a specific directory.
    
    Use this tool to browse the structure of your Obsidian vault and discover
    what notes are available. Can list all notes recursively or just those
    in a specific directory.
    
    Args:
        directory: Specific directory to list (optional, defaults to root)
        recursive: Whether to list all subdirectories recursively (default: true)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing the vault structure and note paths
        
    Example:
        >>> await list_notes("Projects", recursive=False, ctx=ctx)
        {
            "directory": "Projects",
            "recursive": false,
            "count": 5,
            "notes": [
                {"path": "Projects/AI Assistant.md", "name": "AI Assistant.md"},
                {"path": "Projects/Web App.md", "name": "Web App.md"}
            ],
            "folders": ["Projects/Archive", "Projects/Active"]
        }
    """
    if ctx:
        if directory:
            ctx.info(f"Listing notes in: {directory}")
        else:
            ctx.info("Listing all notes in vault")
    
    api = ObsidianAPI()
    
    # Get vault structure for the specified directory or root
    if directory:
        directory = directory.strip("/")
        try:
            vault_items = await api.get_vault_structure(directory)
        except Exception:
            # If directory doesn't exist or error, return empty
            vault_items = []
    else:
        vault_items = await api.get_vault_structure()
    
    # Extract notes and folders
    notes = []
    folders = set()
    
    def process_item(item: VaultItem, parent_path: str = ""):
        """Recursively process vault items."""
        # When getting a specific directory, paths are relative to that directory
        full_path = f"{directory}/{item.path}" if directory else item.path
        
        if item.is_folder:
            folders.add(full_path)
            if recursive and item.children:
                for child in item.children:
                    process_item(child, item.path)
        elif is_markdown_file(full_path):
            notes.append({
                "path": full_path,
                "name": item.name
            })
    
    for item in vault_items:
        process_item(item)
    
    # Sort results
    notes.sort(key=lambda x: x["path"])
    folders = sorted(list(folders))
    
    result = {
        "directory": directory or "/",
        "recursive": recursive,
        "count": len(notes),
        "notes": notes
    }
    
    # Only include folders if not recursive (to avoid clutter)
    if not recursive:
        result["folders"] = folders
    
    return result