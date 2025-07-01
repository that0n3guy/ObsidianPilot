"""Fast search tools using FTS5 full-text search."""

import logging
from typing import Dict, Any, Optional
from ..utils.fts_search import get_fts_search, rebuild_fts_index, QueryParser
from ..utils.filesystem import get_vault
from ..utils.validation import validate_context_length

logger = logging.getLogger(__name__)


async def search_notes(
    query: str,
    max_results: int = 50,
    context_length: int = 100,
    ctx=None
) -> Dict[str, Any]:
    """
    Fast full-text search using SQLite FTS5 for superior performance.
    
    This tool provides blazing-fast search with support for boolean operators,
    phrase search, and proper ranking. Ideal for large vaults where the regular
    search_notes tool becomes slow.
    
    Search Syntax:
    - Simple search: "machine learning" (phrase search)
    - Boolean AND: "python AND tutorial" 
    - Boolean OR: "python OR javascript"
    - Boolean NOT: "python NOT snake"
    - Exact phrase: "machine learning algorithms"
    - Complex: "(python OR ruby) AND tutorial"
    
    Performance Benefits:
    - 100-1000x faster than regular search on large vaults
    - Uses SQLite FTS5 full-text indexing
    - Proper relevance ranking
    - Optimized for vaults with 1000+ notes
    
    Args:
        query: Search query with optional boolean operators
        max_results: Maximum number of results to return (1-500, default: 50)
        context_length: Characters to show around matches (default: 100)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing fast search results with ranking and context
        
    Examples:
        >>> # Simple phrase search
        >>> await search_notes("machine learning", ctx=ctx)
        
        >>> # Boolean search
        >>> await search_notes("python AND (tutorial OR guide)", ctx=ctx)
        
        >>> # Search for any of multiple terms
        >>> await search_notes("Eide Bailly OR CPA OR accounting", ctx=ctx)
        
    When to use:
    - Large vaults (500+ notes) where regular search is slow
    - Complex boolean queries
    - When you need properly ranked results
    - Searching for multiple alternative terms
    
    When NOT to use:
    - Small vaults (regular search_notes is fine)
    - Tag-specific searches (use search_notes with tag: prefix)
    - Property-specific searches (use search_notes with property: prefix)
    """
    # Handle legacy search syntax for backward compatibility
    if query.startswith("tag:"):
        # Convert tag search to fast field search
        tag = query[4:].lstrip("#")
        if ctx:
            ctx.info(f"Converting tag search to fast field search: {tag}")
        return await search_by_field("tags", tag, max_results, ctx)
    elif query.startswith("path:"):
        # Convert path search to fast filename search
        path_pattern = query[5:]
        if ctx:
            ctx.info(f"Converting path search to fast filename search: {path_pattern}")
        return await search_by_field("filename", path_pattern, max_results, ctx)
    elif query.startswith("property:"):
        # Delegate to search_by_property for complex property queries
        if ctx:
            ctx.info(f"Delegating to search_by_property tool for: {query}")
        # Parse property:name:value format
        parts = query.split(":", 2)
        if len(parts) >= 2:
            property_name = parts[1]
            value = parts[2] if len(parts) > 2 else None
            from .search_discovery import search_by_property
            return await search_by_property(property_name, value, "=", context_length, ctx)
        else:
            raise ValueError("Invalid property search format. Use 'property:name:value'")
    
    # Validate inputs for regular fast search
    is_valid, error = QueryParser.validate_query(query)
    if not is_valid:
        raise ValueError(error)
        
    is_valid, error = validate_context_length(context_length)
    if not is_valid:
        raise ValueError(error)
        
    if max_results < 1 or max_results > 500:
        raise ValueError("max_results must be between 1 and 500")
    
    if ctx:
        ctx.info(f"Fast searching with query: {query}")
    
    try:
        # Start background indexing on first use
        from ..server import start_background_index
        await start_background_index()
        
        # Get FTS search engine
        fts = await get_fts_search()
        
        # Check if index exists
        stats = await fts.get_stats()
        if stats["total_files"] == 0:
            # No index yet - return helpful message instead of hanging
            return {
                "results": [],
                "total_count": 0,
                "max_results": max_results,
                "query": {
                    "text": query,
                    "context_length": context_length,
                    "type": "fts5_full_text"
                },
                "performance": {
                    "search_engine": "SQLite FTS5",
                    "indexed_files": 0,
                    "status": "index_not_ready"
                },
                "message": "Search index is not ready. Please use 'rebuild_search_index_tool' first to build the index (this may take 2-5 minutes for large vaults). After indexing, searches will be instant.",
                "truncated": False
            }
        
        # Perform fast search
        results = await fts.search(
            query=query,
            limit=max_results,
            snippet_length=context_length // 3  # FTS5 snippet length is in tokens
        )
        
        # Get search statistics
        stats = await fts.get_stats()
        
        return {
            "results": results,
            "total_count": len(results),
            "max_results": max_results,
            "query": {
                "text": query,
                "context_length": context_length,
                "type": "fts5_full_text"
            },
            "performance": {
                "search_engine": "SQLite FTS5",
                "indexed_files": stats["total_files"],
                "index_age_seconds": stats["index_age_seconds"]
            },
            "truncated": len(results) >= max_results
        }
        
    except Exception as e:
        logger.error(f"Fast search failed for query '{query}': {e}")
        raise ValueError(f"Search failed: {str(e)}")


async def search_by_field(
    field: str,
    value: str,
    max_results: int = 50,
    ctx=None
) -> Dict[str, Any]:
    """
    Search within specific fields like filename, tags, or properties.
    
    This tool allows targeted searching within specific parts of your notes
    using the fast FTS5 index for optimal performance.
    
    Args:
        field: Field to search in ('filename', 'tags', 'properties', 'content')
        value: Value to search for in the specified field
        max_results: Maximum number of results (1-200, default: 50)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing field-specific search results
        
    Examples:
        >>> # Search in filenames only
        >>> await search_by_field("filename", "README", ctx=ctx)
        
        >>> # Search in tags only  
        >>> await search_by_field("tags", "project", ctx=ctx)
        
        >>> # Search in properties only
        >>> await search_by_field("properties", "status:active", ctx=ctx)
        
    Supported Fields:
    - filename: Search note titles/filenames
    - tags: Search note tags
    - properties: Search frontmatter properties
    - content: Search note content (same as search_notes)
    """
    # Validate inputs
    valid_fields = ['filename', 'tags', 'properties', 'content']
    if field not in valid_fields:
        raise ValueError(f"Field must be one of: {', '.join(valid_fields)}")
        
    is_valid, error = QueryParser.validate_query(value)
    if not is_valid:
        raise ValueError(error)
        
    if max_results < 1 or max_results > 200:
        raise ValueError("max_results must be between 1 and 200")
    
    if ctx:
        ctx.info(f"Searching field '{field}' for: {value}")
    
    try:
        # Get FTS search engine
        fts = await get_fts_search()
        
        # Create field-specific query
        if field == 'content':
            fts_query = value
        else:
            # Search within specific field
            fts_query = f'{field}:"{value}"'
        
        # Perform search
        results = await fts.search(
            query=fts_query,
            limit=max_results
        )
        
        return {
            "results": results,
            "total_count": len(results),
            "max_results": max_results,
            "query": {
                "field": field,
                "value": value,
                "type": "field_search"
            },
            "truncated": len(results) >= max_results
        }
        
    except Exception as e:
        logger.error(f"Field search failed for {field}='{value}': {e}")
        raise ValueError(f"Field search failed: {str(e)}")


async def rebuild_search_index(ctx=None) -> Dict[str, Any]:
    """
    Rebuild the fast search index from scratch in the background.
    
    Use this tool when:
    - Search results seem outdated or incomplete
    - After making major changes to your vault
    - If search is returning errors
    - First time using search tools
    
    This starts the index rebuild in the background and returns immediately.
    The rebuild happens asynchronously without blocking the AI assistant.
    
    Args:
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary confirming the rebuild was started
        
    Examples:
        >>> # Start background index rebuild
        >>> await rebuild_search_index(ctx=ctx)
    """
    if ctx:
        ctx.info("Starting background search index rebuild...")
    
    try:
        # Get vault info for estimation
        from ..utils.filesystem import get_vault as get_vault_instance
        vault = get_vault_instance()
        all_notes = await vault.list_notes(recursive=True)
        total_notes = len(all_notes)
        estimated_time = max(1, (total_notes / 1000) * 2)  # 2 min per 1000 notes, min 1 min
        
        # Start rebuild in background (fire and forget)
        import asyncio
        asyncio.create_task(rebuild_fts_index())
        
        if ctx:
            ctx.info(f"Background rebuild started for {total_notes} notes")
        
        return {
            "success": True,
            "status": "rebuild_started",
            "total_notes": total_notes,
            "estimated_time_minutes": round(estimated_time, 1),
            "message": f"Index rebuild started in background for {total_notes} notes. This will take approximately {round(estimated_time, 1)} minutes. You can continue using other tools while the rebuild happens.",
            "background_process": True,
            "next_steps": "The search index will be updated automatically. You can use 'get_search_stats_tool' to check progress."
        }
        
    except Exception as e:
        logger.error(f"Failed to start index rebuild: {e}")
        raise ValueError(f"Failed to start search index rebuild: {str(e)}")


async def get_search_stats(ctx=None) -> Dict[str, Any]:
    """
    Get statistics about the fast search index.
    
    Provides information about the current state of the search index
    including how many files are indexed and when it was last updated.
    
    Args:
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary with search index statistics
        
    Examples:
        >>> # Check search index status
        >>> await get_search_stats(ctx=ctx)
    """
    try:
        fts = await get_fts_search()
        stats = await fts.get_stats()
        
        # Calculate index freshness
        if stats["index_age_seconds"] < 60:
            freshness = "very fresh (< 1 minute)"
        elif stats["index_age_seconds"] < 3600:
            freshness = f"fresh ({stats['index_age_seconds']//60} minutes old)"
        elif stats["index_age_seconds"] < 86400:
            freshness = f"moderate ({stats['index_age_seconds']//3600} hours old)"
        else:
            freshness = f"stale ({stats['index_age_seconds']//86400} days old)"
        
        return {
            "total_indexed_files": stats["total_files"],
            "total_content_size_bytes": stats["total_size_bytes"],
            "total_content_size_mb": round(stats["total_size_bytes"] / 1024 / 1024, 2),
            "index_age_seconds": stats["index_age_seconds"],
            "index_freshness": freshness,
            "search_engine": "SQLite FTS5",
            "status": "ready" if stats["total_files"] > 0 else "empty",
            "recommendation": (
                "Index is ready for searching" if stats["index_age_seconds"] < 3600
                else "Consider rebuilding index if search results seem outdated"
            )
        }
        
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "recommendation": "Try rebuilding the search index"
        }


# Legacy alias for backward compatibility
fast_search_notes = search_notes