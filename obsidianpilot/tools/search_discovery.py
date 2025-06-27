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


async def search_notes(
    query: str,
    context_length: int = 100,
    ctx=None
) -> dict:
    """
    Search for notes containing specific text or matching search criteria.
    
    Use this tool to find notes by content, title, metadata, or properties. Supports
    multiple search modes with special prefixes:
    
    Search Syntax:
    - Content search (default): Just type your query to search within note content
      Example: "machine learning" finds notes containing this text
    - Path/Title search: Use "path:" prefix to search by filename or folder
      Example: "path:Daily/" finds all notes in Daily folder
      Example: "path:Note with Images" finds notes with this in their filename
    - Tag search: Use "tag:" prefix to search by tags
      Example: "tag:project" or "tag:#project" finds notes with the project tag
    - Property search: Use "property:" prefix to search by frontmatter properties
      Example: "property:status:active" finds notes where status = active
      Example: "property:priority:>2" finds notes where priority > 2
      Example: "property:assignee:*john*" finds notes where assignee contains "john"
      Example: "property:deadline:*" finds notes that have a deadline property
    - Combined searches are supported but limited to one mode at a time
    
    Property Operators:
    - ":" or "=" for exact match (property:name:value)
    - ">" for greater than (property:priority:>3)
    - "<" for less than (property:age:<30)
    - ">=" for greater or equal (property:score:>=80)
    - "<=" for less or equal (property:rating:<=5)
    - "!=" for not equal (property:status:!=completed)
    - "*value*" for contains (property:title:*project*)
    - "*" for exists (property:tags:*)
    
    Args:
        query: Search query with optional prefix (path:, tag:, property:, or plain text)
        context_length: Number of characters to show around matches (default: 100)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing search results with matched notes and context
        
    Examples:
        >>> # Search by content
        >>> await search_notes("machine learning algorithms", ctx=ctx)
        
        >>> # Search by filename/path
        >>> await search_notes("path:Project Notes", ctx=ctx)
        
        >>> # Search by tag
        >>> await search_notes("tag:important", ctx=ctx)
        
        >>> # Search by property
        >>> await search_notes("property:status:active", ctx=ctx)
        >>> await search_notes("property:priority:>2", ctx=ctx)
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
    
    vault = get_vault()
    
    try:
        # Handle special search syntax
        if query.startswith("tag:"):
            # Tag search
            tag = query[4:].lstrip("#")
            results = await _search_by_tag(vault, tag, context_length)
        elif query.startswith("path:"):
            # Path search
            path_pattern = query[5:]
            results = await _search_by_path(vault, path_pattern, context_length)
        elif query.startswith("property:"):
            # Property search
            results = await _search_by_property(vault, query, context_length)
        else:
            # Regular content search
            results = await vault.search_notes(query, context_length)
        
        # Return standardized search results structure
        return {
            "results": results,
            "count": len(results),
            "query": {
                "text": query,
                "context_length": context_length,
                "type": "tag" if query.startswith("tag:") else "path" if query.startswith("path:") else "property" if query.startswith("property:") else "content"
            },
            "truncated": False  # We don't have a hard limit on results currently
        }
    except Exception as e:
        if ctx:
            ctx.info(f"Search failed: {str(e)}")
        # Return standardized error structure
        return {
            "results": [],
            "count": 0,
            "query": {
                "text": query,
                "context_length": context_length,
                "type": "tag" if query.startswith("tag:") else "path" if query.startswith("path:") else "property" if query.startswith("property:") else "content"
            },
            "truncated": False,
            "error": f"Search failed: {str(e)}"
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
    Search for notes by their frontmatter property values.
    
    This tool allows advanced filtering of notes based on YAML frontmatter properties,
    supporting various comparison operators and data types.
    
    Args:
        property_name: Name of the property to search for
        value: Value to compare against (optional for 'exists' operator)
        operator: Comparison operator (=, !=, >, <, >=, <=, contains, exists)
        context_length: Characters of note content to include in results
        ctx: MCP context for progress reporting
        
    Operators:
    - "=" or "equals": Exact match (case-insensitive)
    - "!=": Not equal
    - ">": Greater than (numeric/date comparison)
    - "<": Less than (numeric/date comparison)
    - ">=": Greater or equal
    - "<=": Less or equal
    - "contains": Property value contains the search value
    - "exists": Property exists (value parameter ignored)
    
    Returns:
        Dictionary with search results including property values
        
    Examples:
        >>> # Find all notes with status = "active"
        >>> await search_by_property("status", "active", "=")
        
        >>> # Find notes with priority > 2
        >>> await search_by_property("priority", "2", ">")
        
        >>> # Find notes that have a deadline property
        >>> await search_by_property("deadline", operator="exists")
        
        >>> # Find notes where title contains "project"
        >>> await search_by_property("title", "project", "contains")
    """
    if ctx:
        ctx.info(f"Searching by property: {property_name} {operator} {value}")
    
    # Validate operator
    valid_operators = ["=", "equals", "!=", ">", "<", ">=", "<=", "contains", "exists"]
    if operator not in valid_operators:
        raise ValueError(f"Invalid operator: {operator}. Must be one of: {', '.join(valid_operators)}")
    
    # Normalize operator
    if operator == "equals":
        operator = "="
    
    # Build query string for internal function
    if operator == "exists":
        query = f"property:{property_name}:*"
    elif operator == "contains":
        query = f"property:{property_name}:*{value}*"
    elif operator in [">", "<", ">=", "<=", "!="]:
        query = f"property:{property_name}:{operator}{value}"
    else:  # = operator
        query = f"property:{property_name}:{value}"
    
    vault = get_vault()
    
    try:
        results = await _search_by_property(vault, query, context_length)
        
        # Sort results by property value if numeric
        if results and operator in [">", "<", ">=", "<="]:
            try:
                # Try to sort numerically
                results.sort(key=lambda x: float(x.get("property_value", 0)), reverse=(operator in [">", ">="]))
            except:
                # Fall back to string sort
                results.sort(key=lambda x: str(x.get("property_value", "")))
        
        # Return standardized search results structure
        return {
            "results": results,
            "count": len(results),
            "query": {
                "property": property_name,
                "operator": operator,
                "value": value,
                "context_length": context_length
            },
            "truncated": False
        }
    except Exception as e:
        if ctx:
            ctx.info(f"Property search failed: {str(e)}")
        # Return standardized error structure
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


async def search_by_regex(
    pattern: str,
    flags: Optional[List[str]] = None,
    context_length: int = 100,
    max_results: int = 50,
    ctx=None
) -> dict:
    """
    Search for notes using regular expressions for advanced pattern matching.
    
    Use this tool instead of search_notes when you need to find:
    - Code patterns (function definitions, imports, specific syntax)
    - Structured data with specific formats
    - Complex patterns that simple text search can't handle
    - Text with wildcards or variable parts
    
    When to use regex search vs regular search:
    - Use search_notes for: Simple text, note titles (with path:), tags
    - Use search_by_regex for: Code patterns, formatted data, complex matching
    
    Args:
        pattern: Regular expression pattern to search for
        flags: List of regex flags to apply (optional). Supported flags:
               - "ignorecase" or "i": Case-insensitive matching
               - "multiline" or "m": ^ and $ match line boundaries  
               - "dotall" or "s": . matches newlines
        context_length: Number of characters to show around matches (default: 100)
        max_results: Maximum number of results to return (default: 50)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing search results with matched patterns, line numbers, and context
        
    Common Use Cases:
        # Find Python imports of a specific module
        pattern: r"(import|from)\\s+fastmcp"
        
        # Find function definitions
        pattern: r"def\\s+\\w+\\s*\\([^)]*\\):"
        
        # Find TODO/FIXME comments with context
        pattern: r"(TODO|FIXME)\\s*:?\\s*(.+)"
        
        # Find URLs in notes
        pattern: r"https?://[^\\s)>]+"
        
        # Find code blocks of specific language
        pattern: r"```python([^`]+)```"
        
    Example:
        >>> # Find Python function definitions with 'search' in the name
        >>> await search_by_regex(r"def\\s+\\w*search\\w*\\s*\\([^)]*\\):", flags=["ignorecase"])
        {
            "pattern": "def\\s+\\w*search\\w*\\s*\\([^)]*\\):",
            "count": 3,
            "results": [
                {
                    "path": "code/search_utils.py",
                    "match_count": 2,
                    "matches": [
                        {
                            "match": "def search_notes(query, limit):",
                            "line": 15,
                            "context": "...async def search_notes(query, limit):\\n    '''Search through all notes'''...",
                            "groups": null
                        }
                    ]
                }
            ]
        }
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
        # Perform regex search
        results = await vault.search_by_regex(pattern, regex_flags, context_length, max_results)
        
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
        
        # Return standardized search results structure
        return {
            "results": formatted_results,
            "count": len(formatted_results),
            "query": {
                "pattern": pattern,
                "flags": flags or [],
                "context_length": context_length,
                "max_results": max_results
            },
            "truncated": len(results) == max_results  # True if we hit the limit
        }
        
    except ValueError as e:
        # Re-raise validation errors
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
                "max_results": max_results
            },
            "truncated": False,
            "error": f"Regex search failed: {str(e)}"
        }