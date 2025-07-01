"""Search and discovery tools for Obsidian MCP server."""

import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from ..utils.filesystem import get_vault
from ..utils import is_markdown_file
from ..utils.validation import (
    validate_search_query,
    validate_context_length,
    validate_date_search_params,
    validate_directory_path
)
from ..models import VaultItem
from ..constants import ERROR_MESSAGES

logger = logging.getLogger(__name__)


async def _search_by_tag(vault, tag: str, context_length: int) -> List[Dict[str, Any]]:
    """Search for notes containing a specific tag, supporting hierarchical tags."""
    results = []
    
    # Get all notes
    all_notes = await vault.list_notes(recursive=True)
    
    # For large vaults, try fast search first
    if len(all_notes) > 500:
        try:
            from ..tools.fast_search import search_by_field
            fast_result = await search_by_field("tags", tag, max_results=100)
            
            # Convert to legacy format if we got results
            if fast_result['results']:
                for item in fast_result['results']:
                    results.append({
                        "path": item["path"],
                        "score": item["score"],
                        "matches": [f"#{tag}"],
                        "context": item["context"]
                    })
                return results
        except Exception:
            # Fall back to manual search if fast search fails
            pass
    
    for note_info in all_notes:
        try:
            # Read the note to get its tags
            note = await vault.read_note(note_info["path"])
            
            # Check for exact match or hierarchical match
            # For hierarchical tags, we support:
            # - Exact match: "parent/child" matches "parent/child"
            # - Parent match: "parent" matches "parent/child", "parent/grandchild"
            # - Child match: searching for "child" finds "parent/child"
            matched = False
            matching_tags = []
            
            for note_tag in note.metadata.tags:
                # Exact match
                if note_tag == tag:
                    matched = True
                    matching_tags.append(note_tag)
                # Parent tag match - if searching for "parent", match "parent/child"
                elif note_tag.startswith(tag + "/"):
                    matched = True
                    matching_tags.append(note_tag)
                # Child tag match - if searching for "child", match "parent/child"
                elif "/" in note_tag and note_tag.split("/")[-1] == tag:
                    matched = True
                    matching_tags.append(note_tag)
                # Any level match - if searching for "middle", match "parent/middle/child"
                elif "/" in note_tag and f"/{tag}/" in f"/{note_tag}/":
                    matched = True
                    matching_tags.append(note_tag)
            
            if matched:
                # Get context around the tag occurrences
                content = note.content
                contexts = []
                
                # Search for all matching tags in content
                for matched_tag in matching_tags:
                    tag_pattern = f"#{matched_tag}"
                    idx = 0
                    while True:
                        idx = content.find(tag_pattern, idx)
                        if idx == -1:
                            break
                        
                        # Extract context
                        start = max(0, idx - context_length // 2)
                        end = min(len(content), idx + len(tag_pattern) + context_length // 2)
                        context = content[start:end].strip()
                        contexts.append(context)
                        idx += 1
                
                results.append({
                    "path": note.path,
                    "score": 1.0,
                    "matches": matching_tags,
                    "context": " ... ".join(contexts) if contexts else f"Note contains tags: {', '.join(f'#{t}' for t in matching_tags)}"
                })
        except Exception:
            # Skip notes we can't read
            continue
    
    return results


async def _search_by_path(vault, path_pattern: str, context_length: int) -> List[Dict[str, Any]]:
    """Search for notes matching a path pattern."""
    results = []
    
    # Get all notes
    all_notes = await vault.list_notes(recursive=True)
    
    for note_info in all_notes:
        # Check if path matches pattern
        if path_pattern.lower() in note_info["path"].lower():
            try:
                # Read note to get some content for context
                note = await vault.read_note(note_info["path"])
                
                # Get first N characters as context
                context = note.content[:context_length].strip()
                if len(note.content) > context_length:
                    context += "..."
                
                results.append({
                    "path": note.path,
                    "score": 1.0,
                    "matches": [path_pattern],
                    "context": context
                })
            except Exception:
                # If we can't read, still include in results
                results.append({
                    "path": note_info["path"],
                    "score": 1.0,
                    "matches": [path_pattern],
                    "context": ""
                })
    
    return results


def _parse_property_query(query: str) -> Dict[str, Any]:
    """
    Parse a property query string into components.
    
    Supports formats:
    - property:name:value (exact match)
    - property:name:>value (comparison)
    - property:name:*value* (contains)
    - property:name:* (exists)
    
    Returns:
        Dict with 'name', 'operator', and 'value'
    """
    # Remove 'property:' prefix
    prop_query = query[9:]  # len('property:') = 9
    
    # Split by first colon to separate name from value/operator
    parts = prop_query.split(':', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid property query format: {query}")
    
    name = parts[0]
    value_part = parts[1]
    
    # Check for operators
    if value_part == '*':
        return {'name': name, 'operator': 'exists', 'value': None}
    elif value_part.startswith('>='):
        return {'name': name, 'operator': '>=', 'value': value_part[2:]}
    elif value_part.startswith('<='):
        return {'name': name, 'operator': '<=', 'value': value_part[2:]}
    elif value_part.startswith('!='):
        return {'name': name, 'operator': '!=', 'value': value_part[2:]}
    elif value_part.startswith('>'):
        return {'name': name, 'operator': '>', 'value': value_part[1:]}
    elif value_part.startswith('<'):
        return {'name': name, 'operator': '<', 'value': value_part[1:]}
    elif value_part.startswith('*') and value_part.endswith('*'):
        return {'name': name, 'operator': 'contains', 'value': value_part[1:-1]}
    else:
        return {'name': name, 'operator': '=', 'value': value_part}


async def _search_by_property(vault, property_query: str, context_length: int) -> List[Dict[str, Any]]:
    """Search for notes by property values."""
    # Parse the property query
    try:
        parsed = _parse_property_query(property_query)
    except ValueError as e:
        raise ValueError(str(e))
    
    prop_name = parsed['name']
    operator = parsed['operator']
    value = parsed['value']
    
    # Check if we can use the persistent index for property search
    if hasattr(vault, 'persistent_index') and vault.persistent_index:
        try:
            # Use persistent index for efficient property search
            results_from_index = await vault.persistent_index.search_by_property(
                prop_name, operator, value, 200  # Get more results to filter
            )
            
            results = []
            for file_info in results_from_index:
                filepath = file_info['filepath']
                content = file_info['content']
                prop_value = file_info['property_value']
                
                # Create context showing the property
                context = f"{prop_name}: {prop_value}"
                if content:
                    # Add some note content too
                    content_preview = content[:context_length].strip()
                    if len(content) > context_length:
                        content_preview += "..."
                    context = f"{context}\n\n{content_preview}"
                
                results.append({
                    "path": filepath,
                    "score": 1.0,
                    "matches": [f"{prop_name} {operator} {value if value else 'exists'}"],
                    "context": context,
                    "property_value": prop_value
                })
            
            return results
        except Exception as e:
            # Fall back to manual search if index fails
            logger.warning(f"Property search via index failed: {e}, falling back to manual search")
    
    # Fall back to manual search (original implementation)
    results = []
    all_notes = await vault.list_notes(recursive=True)
    
    # Add timeout protection for large vaults
    if len(all_notes) > 500:
        logger.warning(f"Property search on large vault ({len(all_notes)} notes) may be slow. Consider using search_notes_tool instead.")
    
    for note_info in all_notes:
        try:
            # Read note to get metadata
            note = await vault.read_note(note_info["path"])
            
            # Get the property value from frontmatter
            frontmatter = note.metadata.frontmatter
            if prop_name not in frontmatter:
                # Property doesn't exist
                if operator == 'exists':
                    continue  # Skip since we want it to exist
                else:
                    continue  # Skip since property is not present
            
            prop_value = frontmatter[prop_name]
            
            # Check if property exists (special case)
            if operator == 'exists':
                matches = True
            # Handle comparison operators
            elif operator == '=':
                # Handle array/list properties
                if isinstance(prop_value, list):
                    # Check if value is in the list
                    matches = any(str(item).lower() == str(value).lower() for item in prop_value)
                else:
                    matches = str(prop_value).lower() == str(value).lower()
            elif operator == '!=':
                if isinstance(prop_value, list):
                    # Check if value is NOT in the list
                    matches = not any(str(item).lower() == str(value).lower() for item in prop_value)
                else:
                    matches = str(prop_value).lower() != str(value).lower()
            elif operator == 'contains':
                if isinstance(prop_value, list):
                    # Check if any item in list contains the value
                    matches = any(str(value).lower() in str(item).lower() for item in prop_value)
                else:
                    matches = str(value).lower() in str(prop_value).lower()
            elif operator in ['>', '<', '>=', '<=']:
                # For arrays, compare the length
                if isinstance(prop_value, list):
                    try:
                        num_prop = len(prop_value)
                        num_val = float(value)
                        if operator == '>':
                            matches = num_prop > num_val
                        elif operator == '<':
                            matches = num_prop < num_val
                        elif operator == '>=':
                            matches = num_prop >= num_val
                        elif operator == '<=':
                            matches = num_prop <= num_val
                    except (ValueError, TypeError):
                        matches = False
                else:
                    # Try date/datetime comparison first
                    try:
                        # Try common date formats
                        date_prop = None
                        date_val = None
                        
                        # Try ISO format first (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
                        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                date_prop = datetime.strptime(str(prop_value), fmt)
                                date_val = datetime.strptime(str(value), fmt)
                                break
                            except:
                                continue
                        
                        if date_prop and date_val:
                            if operator == '>':
                                matches = date_prop > date_val
                            elif operator == '<':
                                matches = date_prop < date_val
                            elif operator == '>=':
                                matches = date_prop >= date_val
                            elif operator == '<=':
                                matches = date_prop <= date_val
                        else:
                            raise ValueError("Not a date")
                    except:
                        # Try numeric comparison
                        try:
                            num_prop = float(prop_value)
                            num_val = float(value)
                            if operator == '>':
                                matches = num_prop > num_val
                            elif operator == '<':
                                matches = num_prop < num_val
                            elif operator == '>=':
                                matches = num_prop >= num_val
                            elif operator == '<=':
                                matches = num_prop <= num_val
                        except (ValueError, TypeError):
                            # Fall back to string comparison
                            if operator == '>':
                                matches = str(prop_value) > str(value)
                            elif operator == '<':
                                matches = str(prop_value) < str(value)
                            elif operator == '>=':
                                matches = str(prop_value) >= str(value)
                            elif operator == '<=':
                                matches = str(prop_value) <= str(value)
            else:
                matches = False
            
            if matches:
                # Create context showing the property
                if isinstance(prop_value, list):
                    # Format list values nicely
                    context = f"{prop_name}: [{', '.join(str(v) for v in prop_value)}]"
                else:
                    context = f"{prop_name}: {prop_value}"
                if note.content:
                    # Add some note content too
                    content_preview = note.content[:context_length].strip()
                    if len(note.content) > context_length:
                        content_preview += "..."
                    context = f"{context}\n\n{content_preview}"
                
                results.append({
                    "path": note.path,
                    "score": 1.0,
                    "matches": [f"{prop_name} {operator} {value if value else 'exists'}"],
                    "context": context,
                    "property_value": prop_value
                })
        except Exception:
            # Skip notes we can't read
            continue
    
    return results


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
    
    vault = get_vault()
    
    try:
        # Get all notes in the vault
        all_notes = await vault.list_notes(recursive=True)
        
        # Filter by date
        formatted_results = []
        for note_info in all_notes:
            note_path = note_info["path"]
            
            # Get file stats (use lenient path validation for existing files)
            full_path = vault._get_absolute_path(note_path)
            stat = full_path.stat()
            
            # Get the appropriate timestamp
            if date_type == "created":
                timestamp = stat.st_ctime
            else:
                timestamp = stat.st_mtime
            
            file_date = datetime.fromtimestamp(timestamp)
            
            # Check if it matches our criteria
            if operator == "within":
                if file_date >= start_date:
                    days_diff = (now - file_date).days
                    formatted_results.append({
                        "path": note_path,
                        "date": file_date.isoformat(),
                        "days_ago": days_diff
                    })
            else:
                # "exactly" - check if it's on that specific day
                if start_date <= file_date < end_date:
                    days_diff = (now - file_date).days
                    formatted_results.append({
                        "path": note_path,
                        "date": file_date.isoformat(),
                        "days_ago": days_diff
                    })
        
        # Sort by date (most recent first)
        formatted_results.sort(key=lambda x: x["date"], reverse=True)
        
        # Return standardized search results structure
        return {
            "results": formatted_results,
            "count": len(formatted_results),
            "query": {
                "date_type": date_type,
                "days_ago": days_ago,
                "operator": operator,
                "description": query_description
            },
            "truncated": False
        }
        
    except Exception as e:
        if ctx:
            ctx.info(f"Date search failed: {str(e)}")
        # Return standardized error structure
        return {
            "results": [],
            "count": 0,
            "query": {
                "date_type": date_type,
                "days_ago": days_ago,
                "operator": operator,
                "description": query_description
            },
            "truncated": False,
            "error": f"Date-based search failed: {str(e)}"
        }


async def search_by_property(
    property_name: str,
    value: Optional[str] = None,
    operator: str = "=",
    context_length: int = 100,
    ctx=None
) -> dict:
    """
    Search for notes by their frontmatter property values using fast FTS5 search.
    
    This tool provides high-performance filtering of notes based on YAML frontmatter 
    properties. For large vaults, this is dramatically faster than the old implementation.
    
    Args:
        property_name: Name of the property to search for
        value: Value to compare against (optional for 'exists' operator)
        operator: Comparison operator (=, contains, exists) - simplified for fast search
        context_length: Characters of note content to include in results
        ctx: MCP context for progress reporting
        
    Supported Operators (Fast Search):
    - "=" or "equals": Exact match (property:name:value)
    - "contains": Property value contains the search value  
    - "exists": Property exists (searches for property name)
    
    Note: For complex operators (>, <, >=, <=, !=), use the manual search fallback
    or filter results after retrieval for better performance.
    
    Returns:
        Dictionary with search results including property values
        
    Examples:
        >>> # Find all notes with status = "active"
        >>> await search_by_property("status", "active", "=")
        
        >>> # Find notes that have a deadline property
        >>> await search_by_property("deadline", operator="exists")
        
        >>> # Find notes where title contains "project"
        >>> await search_by_property("title", "project", "contains")
    """
    if ctx:
        ctx.info(f"Fast property search: {property_name} {operator} {value}")
    
    # Validate operator
    fast_operators = ["=", "equals", "contains", "exists"]
    complex_operators = [">", "<", ">=", "<=", "!="]
    
    if operator not in fast_operators + complex_operators:
        raise ValueError(f"Invalid operator: {operator}. Supported: {', '.join(fast_operators + complex_operators)}")
    
    # For complex operators, warn about performance and fall back
    if operator in complex_operators:
        if ctx:
            ctx.info(f"Complex operator '{operator}' requires manual search. This may be slower on large vaults.")
        
        # Fall back to original implementation for complex operators
        try:
            vault = get_vault()
            query = f"property:{property_name}:{operator}{value}" if operator != "exists" else f"property:{property_name}:*"
            results = await _search_by_property(vault, query, context_length)
            
            return {
                "results": results,
                "count": len(results),
                "query": {
                    "property": property_name,
                    "operator": operator,
                    "value": value,
                    "context_length": context_length,
                    "search_method": "manual_fallback"
                },
                "truncated": False,
                "performance_note": f"Used manual search for complex operator '{operator}'. For better performance on large vaults, consider using simpler operators."
            }
        except Exception as e:
            if ctx:
                ctx.info(f"Property search failed: {str(e)}")
            return {
                "results": [],
                "count": 0,
                "query": {
                    "property": property_name,
                    "operator": operator,
                    "value": value,
                    "context_length": context_length
                },
                "truncated": False,
                "error": f"Property search failed: {str(e)}"
            }
    
    try:
        # Use fast search for supported operators
        from ..tools.fast_search import search_by_field
        
        # Use direct FTS5 search instead of search_by_field for better control
        from ..utils.fts_search import get_fts_search
        fts = await get_fts_search()
        
        # Build FTS5 query - search for the actual indexed property text
        if operator in ["=", "equals"]:
            # Search for exact "property_name:value" in any field
            fts_query = f'"{property_name}:{value}"'
        elif operator == "contains":
            # Search for property name and value (both should appear)
            fts_query = f'{property_name} AND {value}'
        elif operator == "exists":
            # Just search for the property name followed by colon
            fts_query = f'"{property_name}:"'
        
        # Perform direct FTS5 search
        raw_results = await fts.search(query=fts_query, limit=200)
        
        # Convert to legacy format and add property extraction
        results = []
        for item in raw_results:
            # Try to extract the actual property value from context
            property_value = "found"  # Default if we can't extract
            
            # Look for the property in the snippet/context
            if 'context' in item and f"{property_name}:" in item['context']:
                try:
                    # Simple extraction - look for "property_name: value" pattern
                    lines = item['context'].split('\n')
                    for line in lines:
                        if f"{property_name}:" in line:
                            parts = line.split(f"{property_name}:", 1)
                            if len(parts) > 1:
                                raw_value = parts[1].strip()
                                # Clean up HTML tags from FTS5 snippet highlighting
                                import re
                                cleaned_value = re.sub(r'</?mark>', '', raw_value)
                                property_value = cleaned_value.strip()
                                break
                except:
                    pass
            
            results.append({
                "path": item["path"],
                "score": item.get("score", 1.0),
                "matches": [f"{property_name} {operator} {value if value else 'exists'}"],
                "context": item["context"],
                "property_value": property_value
            })
        
        # Return standardized search results structure
        return {
            "results": results,
            "count": len(results),
            "query": {
                "property": property_name,
                "operator": operator,
                "value": value,
                "context_length": context_length,
                "search_method": "fast_fts5"
            },
            "truncated": len(results) >= 200,
            "performance_note": "Used fast FTS5 search for optimal performance on large vaults."
        }
        
    except Exception as e:
        if ctx:
            ctx.info(f"Fast property search failed, falling back: {str(e)}")
        
        # Fall back to manual search if fast search fails
        try:
            vault = get_vault()
            query = f"property:{property_name}:{value}" if operator != "exists" else f"property:{property_name}:*"
            results = await _search_by_property(vault, query, context_length)
            
            return {
                "results": results,
                "count": len(results),
                "query": {
                    "property": property_name,
                    "operator": operator,
                    "value": value,
                    "context_length": context_length,
                    "search_method": "manual_fallback"
                },
                "truncated": False,
                "performance_note": "Fast search failed, used manual search as fallback."
            }
        except Exception as fallback_error:
            return {
                "results": [],
                "count": 0,
                "query": {
                    "property": property_name,
                    "operator": operator,
                    "value": value,
                    "context_length": context_length
                },
                "truncated": False,
                "error": f"Both fast and manual property search failed: {str(fallback_error)}"
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
    
    vault = get_vault()
    
    try:
        notes = await vault.list_notes(directory, recursive)
        
        # Return standardized list results structure
        return {
            "items": notes,
            "total": len(notes),
            "scope": {
                "directory": directory or "vault root",
                "recursive": recursive
            }
        }
    except Exception as e:
        if ctx:
            ctx.info(f"Failed to list notes: {str(e)}")
        # Return standardized error structure
        return {
            "items": [],
            "total": 0,
            "scope": {
                "directory": directory or "vault root",
                "recursive": recursive
            },
            "error": f"Failed to list notes: {str(e)}"
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
    
    vault = get_vault()
    
    try:
        # Determine search path
        if directory:
            search_path = vault._ensure_safe_path(directory)
            if not search_path.exists() or not search_path.is_dir():
                return {
                    "directory": directory,
                    "recursive": recursive,
                    "count": 0,
                    "folders": []
                }
        else:
            search_path = vault.vault_path
        
        # Find all directories
        folders = []
        if recursive:
            # Recursive search
            for path in search_path.rglob("*"):
                if path.is_dir():
                    rel_path = path.relative_to(vault.vault_path)
                    # Skip hidden directories
                    if not any(part.startswith(".") for part in rel_path.parts):
                        folders.append({
                            "path": str(rel_path),
                            "name": path.name
                        })
        else:
            # Non-recursive - only immediate subdirectories
            for path in search_path.iterdir():
                if path.is_dir():
                    rel_path = path.relative_to(vault.vault_path)
                    # Skip hidden directories
                    if not path.name.startswith("."):
                        folders.append({
                            "path": str(rel_path),
                            "name": path.name
                        })
        
        # Sort by path
        folders.sort(key=lambda x: x["path"])
        
        # Return standardized list results structure
        return {
            "items": folders,
            "total": len(folders),
            "scope": {
                "directory": directory or "vault root",
                "recursive": recursive
            }
        }
    except Exception as e:
        if ctx:
            ctx.info(f"Failed to list folders: {str(e)}")
        # Return standardized error structure
        return {
            "items": [],
            "total": 0,
            "scope": {
                "directory": directory or "vault root",
                "recursive": recursive
            },
            "error": f"Failed to list folders: {str(e)}"
        }


async def _search_by_regex_filtered(vault, notes_list, pattern: str, regex_flags: int, context_length: int, max_results: int) -> List[Dict[str, Any]]:
    """
    Directory-aware regex search that only searches through specified notes.
    Much faster than vault-wide search when directory is specified.
    """
    import re
    
    # Compile regex pattern
    try:
        regex = re.compile(pattern, regex_flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")
    
    results = []
    
    # Search through only the specified notes
    for note_info in notes_list:
        if len(results) >= max_results:
            break
            
        try:
            # Read the note content
            note = await vault.read_note(note_info["path"])
            content = note.content
            
            # Find all matches with their positions
            matches = list(regex.finditer(content))
            
            if matches:
                # Get line numbers for better context
                lines = content.split('\n')
                line_starts = [0]
                for line in lines[:-1]:
                    line_starts.append(line_starts[-1] + len(line) + 1)
                
                # Extract contexts for matches
                match_contexts = []
                for match in matches[:5]:  # Limit to first 5 matches per file
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Find line number
                    line_num = 1  # Start at 1 for human-readable line numbers
                    for i, start in enumerate(line_starts):
                        if start > match_start:
                            line_num = i
                            break
                    else:
                        line_num = len(lines)
                    
                    # Extract context
                    context_start = max(0, match_start - context_length // 2)
                    context_end = min(len(content), match_end + context_length // 2)
                    context = content[context_start:context_end].strip()
                    
                    # Add ellipsis if truncated
                    if context_start > 0:
                        context = "..." + context
                    if context_end < len(content):
                        context = context + "..."
                    
                    match_contexts.append({
                        "match": match.group(0),
                        "line": line_num,
                        "context": context,
                        "groups": match.groups() if match.groups() else None
                    })
                
                results.append({
                    "path": note_info["path"],
                    "match_count": len(matches),
                    "matches": match_contexts,
                    "score": min(len(matches) / 5.0 + 1.0, 5.0)  # Score based on match count
                })
        
        except Exception as e:
            # Skip notes we can't read, but log for debugging
            logger.warning(f"Failed to search in {note_info['path']}: {e}")
            continue
    
    # Sort by score (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


async def search_by_regex(
    pattern: str,
    directory: Optional[str] = None,
    flags: Optional[List[str]] = None,
    context_length: int = 100,
    max_results: int = 50,
    ctx=None
) -> dict:
    """
    Search for notes using regular expressions with performance optimization and directory scoping.
    
    PERFORMANCE NOTE: Regex search can be slow on large vaults (1000+ notes). For better 
    performance, specify a directory to limit the search scope, or use 'search_notes_tool' 
    for simple text searches.
    
    Use this tool when you specifically need regex pattern matching for:
    - Code patterns (function definitions, imports, specific syntax)
    - Structured data with specific formats
    - Complex patterns that simple text search can't handle
    - Text with wildcards or variable parts that require regex
    
    Performance optimizations:
    - **Directory scoping**: Limit search to specific folders for much faster results
    - **Timeout protection**: 30-second timeout to prevent hanging on large vaults
    - **Result limiting**: Automatic limits based on vault size
    - **Smart suggestions**: Suggests faster alternatives when appropriate
    
    Args:
        pattern: Regular expression pattern to search for
        directory: Limit search to specific directory (e.g., "Projects", "Daily") for MUCH better performance
        flags: List of regex flags to apply (optional). Supported flags:
               - "ignorecase" or "i": Case-insensitive matching
               - "multiline" or "m": ^ and $ match line boundaries  
               - "dotall" or "s": . matches newlines
        context_length: Number of characters to show around matches (default: 100)
        max_results: Maximum number of results to return (default: 50, limited for large vaults)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing search results with matched patterns, line numbers, and context
        
    Performance Tips:
        - **Use directory scoping**: search_by_regex("pattern", directory="Projects") 
        - **Limit scope**: Instead of searching 1800+ files, search just 50-100 in a folder
        - **For simple patterns**: Use search_notes_tool("text") instead
        - **For boolean queries**: Use search_notes_tool("term1 AND term2")
        - **For field search**: Use search_by_field_tool("filename", "pattern")
        
    Example Usage:
        # Search entire vault (slow on large vaults)
        await search_by_regex(r"def\\s+\\w+", flags=["ignorecase"])
        
        # Search only Projects folder (much faster!)
        await search_by_regex(r"def\\s+\\w+", directory="Projects") 
        
        # Search specific subfolder
        await search_by_regex(r"TODO", directory="Daily/2024")
        
    Common Regex Patterns:
        # Find Python imports: r"(import|from)\\s+fastmcp"
        # Find functions: r"def\\s+\\w+\\s*\\([^)]*\\):"
        # Find TODOs: r"(TODO|FIXME)\\s*:?\\s*(.+)"
        # Find URLs: r"https?://[^\\s)>]+"
        # Find code blocks: r"```python([^`]+)```"
    """
    # Validate regex pattern
    try:
        # Test compile the pattern
        re.compile(pattern)
    except re.error as e:
        raise ValueError(f"Invalid regular expression pattern: {e}")
    
    # Validate context_length
    is_valid, error = validate_context_length(context_length)
    if not is_valid:
        raise ValueError(error)
    
    # Convert string flags to regex flags
    regex_flags = 0
    if flags:
        flag_map = {
            "ignorecase": re.IGNORECASE,
            "i": re.IGNORECASE,
            "multiline": re.MULTILINE,
            "m": re.MULTILINE,
            "dotall": re.DOTALL,
            "s": re.DOTALL
        }
        for flag in flags:
            if flag.lower() in flag_map:
                regex_flags |= flag_map[flag.lower()]
            else:
                raise ValueError(f"Unknown regex flag: {flag}. Supported flags: ignorecase/i, multiline/m, dotall/s")
    
    if ctx:
        ctx.info(f"Searching with regex pattern: {pattern}")
    
    vault = get_vault()
    
    try:
        # Get notes from specified directory or entire vault
        all_notes = await vault.list_notes(directory=directory, recursive=True)
        vault_size = len(all_notes)
        
        # Log search scope for debugging
        if ctx:
            if directory:
                ctx.info(f"Searching in directory '{directory}': {vault_size} notes")
            else:
                ctx.info(f"Searching entire vault: {vault_size} notes")
        
        # Performance optimization based on search scope
        if not directory and vault_size > 1000:
            # Large vault without directory scoping - apply strict limits
            if ctx:
                ctx.info(f"Large vault detected ({vault_size} notes). Consider using directory parameter for better performance.")
            
            # Suggest directory scoping or fast search alternative
            simple_pattern = _suggest_fast_alternative(pattern, flags)
            if simple_pattern:
                if ctx:
                    ctx.info(f"Performance tips: Use directory='FolderName' or try search_notes_tool('{simple_pattern}')")
            
            # Apply strict limits and timeout for full vault search
            max_results = min(max_results, 10)  # Reduce result limit
            timeout = 20.0  # Shorter timeout
        elif not directory and vault_size > 500:
            # Medium vault without directory scoping
            if ctx:
                ctx.info(f"Medium vault detected ({vault_size} notes). Consider using directory parameter to improve performance.")
            max_results = min(max_results, 20)
            timeout = 30.0
        elif vault_size > 100:
            # Directory scoped or smaller vault - more generous limits
            timeout = 45.0
            max_results = min(max_results, 50)
        else:
            # Small search scope - normal limits
            timeout = 60.0  # Normal timeout for small scopes
        
        # Perform regex search with timeout (directory-aware implementation)
        import asyncio
        try:
            if directory:
                # Use directory-filtered notes for much faster search
                if ctx:
                    ctx.info(f"Using directory-filtered regex search: {vault_size} notes in '{directory}'")
                results = await asyncio.wait_for(
                    _search_by_regex_filtered(vault, all_notes, pattern, regex_flags, context_length, max_results),
                    timeout=timeout
                )
            else:
                # Use vault-wide search for backward compatibility
                if ctx:
                    ctx.info(f"Using vault-wide regex search: {vault_size} notes (entire vault)")
                results = await asyncio.wait_for(
                    vault.search_by_regex(pattern, regex_flags, context_length, max_results),
                    timeout=timeout
                )
        except asyncio.TimeoutError:
            # Return helpful error with alternatives
            error_msg = f"Regex search timed out on large vault ({vault_size} notes, {timeout}s limit)"
            
            simple_alt = _suggest_fast_alternative(pattern, flags)
            if simple_alt:
                error_msg += f". Try search_notes_tool('{simple_alt}') for much better performance"
            else:
                error_msg += ". Consider using search_notes_tool() with simpler boolean queries instead"
            
            raise ValueError(error_msg)
        
        # Format results for output
        formatted_results = []
        for result in results:
            formatted_result = {
                "path": result["path"],
                "match_count": result["match_count"],
                "matches": []
            }
            
            # Include match details
            for match in result["matches"]:
                match_info = {
                    "match": match["match"],
                    "line": match["line"],
                    "context": match["context"]
                }
                
                # Include capture groups if present
                if match["groups"]:
                    match_info["groups"] = match["groups"]
                
                formatted_result["matches"].append(match_info)
            
            formatted_results.append(formatted_result)
        
        # Build response with performance info
        response = {
            "results": formatted_results,
            "count": len(formatted_results),
            "query": {
                "pattern": pattern,
                "flags": flags or [],
                "context_length": context_length,
                "max_results": max_results,
                "directory": directory,
                "search_method": "regex_with_timeout" + ("_directory_filtered" if directory else ""),
                "search_scope": f"{vault_size} notes" + (f" in '{directory}'" if directory else " (entire vault)")
            },
            "truncated": len(results) == max_results
        }
        
        # Add performance note based on search scope
        if not directory and vault_size > 500:
            simple_alt = _suggest_fast_alternative(pattern, flags)
            if simple_alt:
                response["performance_note"] = f"Performance tips: Use directory='FolderName' to limit scope, or try search_notes_tool('{simple_alt}') for simple patterns"
            else:
                response["performance_note"] = "Performance tips: Use directory='FolderName' to limit scope, or try search_notes_tool() with boolean operators for simple searches"
        elif directory:
            response["performance_note"] = f"Directory scoped search: {vault_size} notes in '{directory}' - much faster than full vault search!"
        
        return response
        
    except ValueError as e:
        # Re-raise validation errors and timeout errors
        raise e
    except Exception as e:
        if ctx:
            ctx.info(f"Regex search failed: {str(e)}")
        # Return standardized error structure
        return {
            "results": [],
            "count": 0,
            "query": {
                "pattern": pattern,
                "flags": flags or [],
                "context_length": context_length,
                "max_results": max_results,
                "directory": directory,
                "search_method": "regex_with_timeout"
            },
            "truncated": False,
            "error": f"Regex search failed: {str(e)}"
        }


def _suggest_fast_alternative(pattern: str, flags: Optional[List[str]] = None) -> Optional[str]:
    """Suggest a fast search alternative for simple regex patterns."""
    import re
    
    # Check if case insensitive
    is_case_insensitive = flags and any(f.lower() in ['i', 'ignorecase'] for f in flags)
    
    # Simple word patterns
    simple_word = re.match(r'^\\?w*([a-zA-Z0-9_]+)\\?w*$', pattern)
    if simple_word:
        return simple_word.group(1).lower() if is_case_insensitive else simple_word.group(1)
    
    # Simple text patterns without special chars
    if re.match(r'^[a-zA-Z0-9\s_-]+$', pattern):
        return pattern.lower() if is_case_insensitive else pattern
    
    # Literal strings with escaped special chars
    literal_pattern = re.sub(r'\\(.)', r'\1', pattern)
    if re.match(r'^[a-zA-Z0-9\s_.-]+$', literal_pattern):
        return literal_pattern.lower() if is_case_insensitive else literal_pattern
    
    # Simple OR patterns
    or_match = re.match(r'^\(([^)]+)\)$', pattern)
    if or_match:
        terms = or_match.group(1).split('|')
        if all(re.match(r'^[a-zA-Z0-9_-]+$', term.strip()) for term in terms):
            clean_terms = [term.strip() for term in terms]
            if is_case_insensitive:
                clean_terms = [term.lower() for term in clean_terms]
            return ' OR '.join(clean_terms)
    
    return None