"""Search and discovery tools for Obsidian MCP server."""

from typing import List, Optional
from datetime import datetime, timedelta
from ..utils import ObsidianAPI, is_markdown_file
from ..utils.validation import (
    validate_search_query,
    validate_context_length,
    validate_date_search_params,
    validate_directory_path
)
from ..models import VaultItem
from ..constants import ERROR_MESSAGES


async def search_notes(
    query: str,
    context_length: int = 100,
    ctx=None
) -> dict:
    """
    Search for notes containing specific text or matching search criteria.
    
    Use this tool to find notes by content, title, or metadata. Supports
    Obsidian's search syntax including tags, paths, and content matching.
    
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
    # Validate parameters
    is_valid, error = validate_search_query(query)
    if not is_valid:
        raise ValueError(error)
    
    is_valid, error = validate_context_length(context_length)
    if not is_valid:
        raise ValueError(error)
    
    if ctx:
        ctx.info(f"Searching notes with query: {query}")
    
    api = ObsidianAPI()
    
    try:
        results = await api.search(query)
    except ConnectionError as e:
        # Only catch connection errors, let other errors through for debugging
        if ctx:
            ctx.info(f"Search endpoint unavailable: {str(e)}")
        return {
            "query": query,
            "count": 0,
            "results": [],
            "error": "Search functionality is currently unavailable. Please check if the Obsidian REST API is running and accessible."
        }
    
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
            if context:
                contexts.append(context)
        
        formatted_results.append({
            "path": result.get("path", result.get("filename", "")),
            "score": result.get("score", 1.0),
            "matches": matches,
            "context": " ... ".join(contexts) if contexts else ""
        })
    
    # Sort by score
    formatted_results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "query": query,
        "count": len(formatted_results),
        "results": formatted_results
    }


async def search_by_date(
    date_type: str = "modified",
    days_ago: int = 7,
    operator: str = "within",
    ctx=None
) -> dict:
    """
    Search for notes by creation or modification date.
    
    Use this tool to find notes created or modified within a specific time period.
    This is useful for finding recent work, tracking activity, or reviewing old notes.
    
    Args:
        date_type: Either "created" or "modified" (default: "modified")
        days_ago: Number of days to look back (default: 7)
        operator: Either "within" (last N days) or "exactly" (exactly N days ago) (default: "within")
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing search results with matched notes
        
    Example:
        >>> await search_by_date("modified", 7, "within", ctx=ctx)
        {
            "query": "Notes modified within last 7 days",
            "count": 15,
            "results": [
                {
                    "path": "Daily/2024-01-15.md",
                    "date": "2024-01-15T10:30:00Z",
                    "days_ago": 1
                }
            ]
        }
    """
    # Validate parameters
    is_valid, error = validate_date_search_params(date_type, days_ago, operator)
    if not is_valid:
        raise ValueError(error)
    
    # Calculate the date threshold
    now = datetime.now()
    
    if operator == "within":
        # For "within", we want notes from the start of (now - days_ago) to now
        # Calculate the start of the target day
        target_date = now - timedelta(days=days_ago)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        query_description = f"Notes {date_type} within last {days_ago} days"
    else:
        # For "exactly", we want notes from that specific day
        target_date = now - timedelta(days=days_ago)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        query_description = f"Notes {date_type} exactly {days_ago} days ago"
    
    if ctx:
        ctx.info(f"Searching for {query_description}")
    
    api = ObsidianAPI()
    
    # Use JsonLogic to search by date
    # The stat object contains ctime (created) and mtime (modified) as Unix timestamps
    stat_field = "ctime" if date_type == "created" else "mtime"
    
    # Convert dates to Unix timestamps (milliseconds)
    start_timestamp = int(start_date.timestamp() * 1000)
    
    if operator == "within":
        # Search for notes where stat.mtime >= start_timestamp
        json_logic_query = {
            ">=": [
                {"var": f"stat.{stat_field}"},
                start_timestamp
            ]
        }
    else:
        # Search for notes where start_timestamp <= stat.mtime < end_timestamp
        end_timestamp = int(end_date.timestamp() * 1000)
        json_logic_query = {
            "and": [
                {">=": [{"var": f"stat.{stat_field}"}, start_timestamp]},
                {"<": [{"var": f"stat.{stat_field}"}, end_timestamp]}
            ]
        }
    
    try:
        results = await api.search_with_jsonlogic(json_logic_query)
        
        # Format results with date information
        formatted_results = []
        for result in results:
            # Get the file path
            file_path = result.get("path", result.get("filename", ""))
            
            # Try to get the actual date from the result
            if isinstance(result, dict) and "stat" in result:
                timestamp = result["stat"].get(stat_field, 0) / 1000  # Convert from ms to seconds
                file_date = datetime.fromtimestamp(timestamp)
            else:
                # Fallback: we know it matches our criteria
                file_date = start_date
            
            # Calculate days ago
            days_diff = (now - file_date).days
            
            formatted_results.append({
                "path": file_path,
                "date": file_date.isoformat(),
                "days_ago": days_diff
            })
        
        # Sort by date (most recent first)
        formatted_results.sort(key=lambda x: x["date"], reverse=True)
        
        return {
            "query": query_description,
            "count": len(formatted_results),
            "results": formatted_results
        }
        
    except Exception as e:
        if ctx:
            ctx.info(f"Date search failed: {str(e)}")
        return {
            "query": query_description,
            "count": 0,
            "results": [],
            "error": f"Date-based search is not available: {str(e)}"
        }


async def list_notes(
    directory: Optional[str] = None,
    recursive: bool = True,
    ctx=None
) -> dict:
    """
    List notes in the vault or a specific directory.
    
    Use this tool to browse the vault structure and discover notes. You can list
    all notes or focus on a specific directory. This is helpful when you know
    the general location but not the exact filename.
    
    Args:
        directory: Specific directory to list (optional, defaults to root)
        recursive: Whether to list all subdirectories recursively (default: true)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing vault structure and note paths
        
    Example:
        >>> await list_notes("Projects", recursive=True, ctx=ctx)
        {
            "directory": "Projects",
            "recursive": true,
            "count": 12,
            "notes": [
                {"path": "Projects/Web App.md", "name": "Web App.md"},
                {"path": "Projects/Ideas/AI Assistant.md", "name": "AI Assistant.md"}
            ]
        }
    """
    # Validate directory parameter
    is_valid, error = validate_directory_path(directory)
    if not is_valid:
        raise ValueError(error)
    
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
    
    async def process_directory(dir_path: str = None):
        """Process a directory and optionally recurse into subdirectories."""
        try:
            # Get items for this directory
            items = await api.get_vault_structure(dir_path)
            
            for item in items:
                # Construct full path
                if dir_path:
                    full_path = f"{dir_path}/{item.path}"
                else:
                    full_path = item.path
                
                if item.is_folder:
                    folders.add(full_path)
                    # If recursive, process this folder too
                    if recursive:
                        await process_directory(full_path)
                elif is_markdown_file(full_path):
                    notes.append({
                        "path": full_path,
                        "name": item.name
                    })
        except Exception:
            # Silently skip directories we can't access
            pass
    
    # Start processing from the specified directory or root
    await process_directory(directory)
    
    # Sort results
    notes.sort(key=lambda x: x["path"])
    folders = sorted(list(folders))
    
    return {
        "directory": directory or "/",
        "recursive": recursive,
        "count": len(notes),
        "notes": notes
    }


async def list_folders(
    directory: Optional[str] = None,
    recursive: bool = True,
    ctx=None
) -> dict:
    """
    List folders in the vault or a specific directory.
    
    Use this tool to explore the vault's folder structure. This is helpful for
    verifying folder names before creating notes, understanding the organizational
    hierarchy, or checking if a specific folder exists.
    
    Args:
        directory: Specific directory to list folders from (optional, defaults to root)
        recursive: Whether to include all nested subfolders (default: true)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing folder structure with paths and folder counts
        
    Example:
        >>> await list_folders("Projects", recursive=True, ctx=ctx)
        {
            "directory": "Projects",
            "recursive": true,
            "count": 5,
            "folders": [
                {"path": "Projects/Active", "name": "Active"},
                {"path": "Projects/Archive", "name": "Archive"},
                {"path": "Projects/Ideas", "name": "Ideas"}
            ]
        }
    """
    # Validate directory parameter
    is_valid, error = validate_directory_path(directory)
    if not is_valid:
        raise ValueError(error)
    
    if ctx:
        if directory:
            ctx.info(f"Listing folders in: {directory}")
        else:
            ctx.info("Listing all folders in vault")
    
    api = ObsidianAPI()
    
    # Dictionary to store folders with their metadata
    folders_dict = {}
    
    async def process_directory(dir_path: str = None, depth: int = 0):
        """Process a directory and optionally recurse into subdirectories."""
        try:
            # Get items for this directory
            items = await api.get_vault_structure(dir_path)
            
            for item in items:
                if item.is_folder:
                    # Construct full path
                    if dir_path:
                        full_path = f"{dir_path}/{item.path}"
                    else:
                        full_path = item.path
                    
                    # Store folder information
                    folders_dict[full_path] = {
                        "path": full_path,
                        "name": item.name,
                        "depth": depth
                    }
                    
                    # If recursive, process this folder too
                    if recursive:
                        await process_directory(full_path, depth + 1)
        except Exception:
            # Silently skip directories we can't access
            pass
    
    # Start processing from the specified directory or root
    start_depth = 0
    if directory:
        # When starting from a subdirectory, depth 0 is that directory
        await process_directory(directory, start_depth)
    else:
        await process_directory(None, start_depth)
    
    # Convert to sorted list
    folders = sorted(folders_dict.values(), key=lambda x: x["path"])
    
    # Remove depth from output (was only used for internal tracking)
    for folder in folders:
        folder.pop("depth", None)
    
    return {
        "directory": directory or "/",
        "recursive": recursive,
        "count": len(folders),
        "folders": folders
    }