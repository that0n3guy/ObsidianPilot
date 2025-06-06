"""Search and discovery tools for Obsidian MCP server."""

from typing import List, Optional
from datetime import datetime, timedelta
from ..utils import ObsidianAPI, is_markdown_file
from ..models import VaultItem


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
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
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
    if date_type not in ["created", "modified"]:
        raise ValueError("date_type must be either 'created' or 'modified'")
    
    if operator not in ["within", "exactly"]:
        raise ValueError("operator must be either 'within' or 'exactly'")
    
    if days_ago < 0:
        raise ValueError("days_ago must be a positive number")
    
    # Calculate the date threshold
    now = datetime.now()
    
    if operator == "within":
        # For "within", we want notes from (now - days_ago) to now
        start_date = now - timedelta(days=days_ago)
        query_description = f"Notes {date_type} within last {days_ago} days"
    else:
        # For "exactly", we want notes from that specific day
        start_date = now - timedelta(days=days_ago)
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
    
    return {
        "directory": directory or "/",
        "recursive": recursive,
        "count": len(notes),
        "notes": notes
    }