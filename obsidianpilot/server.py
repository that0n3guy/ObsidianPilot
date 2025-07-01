"""Main entry point for Obsidian MCP server."""

import os
import logging
from typing import Annotated, Optional, List, Literal
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from .utils.filesystem import init_vault

# Configure logging
logging.basicConfig(
    level=os.getenv("OBSIDIAN_LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import all tools
from .tools import (
    read_note,
    create_note,
    update_note,
    delete_note,
    edit_note_section,
    edit_note_content,
    search_by_date,
    search_by_regex,
    search_by_property,
    list_notes,
    list_folders,
    move_note,
    create_folder,
    move_folder,
    add_tags,
    update_tags,
    remove_tags,
    get_note_info,
    list_tags,
    get_backlinks,
    get_outgoing_links,
    find_broken_links,
    read_image,
    view_note_images,
)

# Import fast search tools
from .tools.fast_search import (
    search_notes,
    search_by_field,
    rebuild_search_index,
    get_search_stats,
)

# Check for vault path
if not os.getenv("OBSIDIAN_VAULT_PATH"):
    raise ValueError("OBSIDIAN_VAULT_PATH environment variable must be set")

# Initialize vault
init_vault()

# Background indexing will be started when the server runs
_background_index_started = False

async def start_background_index():
    """Build search index in background on first tool use."""
    global _background_index_started
    if _background_index_started:
        return
    
    _background_index_started = True
    
    try:
        from .utils.fts_search import get_fts_search, rebuild_fts_index
        logger.info("Checking search index status...")
        fts = await get_fts_search()
        stats = await fts.get_stats()
        
        if stats["total_files"] == 0:
            logger.info("No search index found, building in background...")
            # Run indexing in background task
            import asyncio
            asyncio.create_task(rebuild_fts_index())
        else:
            logger.info(f"Search index already exists with {stats['total_files']} files")
            
        # Start background file change monitoring
        from .utils.index_updater import start_index_updater
        await start_index_updater()
    except Exception as e:
        logger.warning(f"Background indexing check failed: {e}")

# Create FastMCP server instance
mcp = FastMCP(
    "obsidian-mcp",
    instructions="MCP server for direct filesystem access to Obsidian vaults"
)

# Register tools with proper error handling
@mcp.tool()
async def read_note_tool(
    path: Annotated[str, Field(
        description="Note location within your vault (e.g., 'Projects/AI Research.md'). Use forward slashes for folders.",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/AI Research.md", "Ideas/Quick Note.md"]
    )],
    ctx=None
):
    """
    Read the content and metadata of a specific note.
    
    When to use:
    - Displaying note contents to the user
    - Analyzing or processing existing note data
    - ALWAYS before updating a note to preserve existing content
    - Verifying a note exists before making changes
    
    When NOT to use:
    - Searching multiple notes (use search_notes instead)
    - Getting only metadata (use get_note_info for efficiency)
    - Viewing images in a note (use view_note_images instead)
    
    Returns:
        Note content and metadata including tags, aliases, and frontmatter.
        Image references (![alt](path)) are preserved in the content but images are not loaded.
        
    IMPORTANT: If the note contains image references, proactively offer to analyze them:
    "I can see this note contains [N] images. Would you like me to analyze/examine them for you?"
    Then use view_note_images to load and analyze the images if requested.
    """
    try:
        return await read_note(path, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to read note: {str(e)}")

@mcp.tool()
async def create_note_tool(
    path: Annotated[str, Field(
        description="Where to create the new note in your vault. Folders will be created automatically if needed.",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Ideas/New Idea.md", "Daily/2024-01-15.md", "Projects/Project Plan.md"]
    )],
    content: Annotated[str, Field(
        description="The markdown content for your note. Can include headings (#), tags (#tag), links ([[other note]]), and frontmatter.",
        min_length=0,
        max_length=1000000,
        examples=[
            "# Meeting Notes\n#meeting #project-alpha\n\nDiscussed timeline and deliverables...",
            "---\ntags: [daily, planning]\n---\n\n# Daily Note\n\nToday's tasks..."
        ]
    )],
    overwrite: Annotated[bool, Field(
        description="Set to true to replace an existing note at this location. Use carefully as this deletes the original content.",
        default=False
    )] = False,
    ctx=None
):
    """
    Create a new note or overwrite an existing one.
    
    When to use:
    - Creating new notes with specific content
    - Setting up templates or structured notes
    - Programmatically generating documentation
    
    When NOT to use:
    - Updating existing notes (use update_note unless you want to replace entirely)
    - Appending content (use update_note with merge_strategy="append")
        
    Returns:
        Created note information with path and metadata
    """
    try:
        return await create_note(path, content, overwrite, ctx)
    except (ValueError, FileExistsError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to create note: {str(e)}")

@mcp.tool()
async def update_note_tool(
    path: Annotated[str, Field(
        description="Which note to update in your vault",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/Project.md"]
    )],
    content: Annotated[str, Field(
        description="New content for the note. By default this REPLACES all existing content. Use merge_strategy='append' to add to the end instead.",
        min_length=0,
        max_length=1000000
    )],
    create_if_not_exists: Annotated[bool, Field(
        description="Automatically create the note if it doesn't exist yet",
        default=False
    )] = False,
    merge_strategy: Annotated[Literal["replace", "append"], Field(
        description="How to handle existing content. 'replace' = overwrite everything (default), 'append' = add new content to the end",
        default="replace"
    )] = "replace",
    ctx=None
):
    """
    Update the content of an existing note.
    
    ⚠️ IMPORTANT: By default, this REPLACES the entire note content.
    Always read the note first if you need to preserve existing content.
    
    When to use:
    - Updating a note with completely new content (replace)
    - Adding content to the end of a note (append)
    - Programmatically modifying notes
    
    When NOT to use:
    - Making small edits (read first, then update with full content)
    - Creating new notes (use create_note instead)
    
    Returns:
        Update status with path, metadata, and operation performed
    """
    try:
        return await update_note(path, content, create_if_not_exists, merge_strategy, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to update note: {str(e)}")

@mcp.tool()
async def delete_note_tool(path: str, ctx=None):
    """
    Delete a note from the vault.
    
    Args:
        path: Path to the note to delete
        
    Returns:
        Deletion status
    """
    try:
        return await delete_note(path, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to delete note: {str(e)}")

@mcp.tool()
async def edit_note_section_tool(
    path: Annotated[str, Field(
        description="Path to the note to edit",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/Website.md", "Notes/Research.md"]
    )],
    section_identifier: Annotated[str, Field(
        description="Markdown heading that identifies the section (e.g., '## Tasks', '### Status'). Case-insensitive matching.",
        min_length=1,
        max_length=100,
        examples=["## Tasks", "### Current Status", "# Main Topic", "#### Details"]
    )],
    content: Annotated[str, Field(
        description="Content to insert, replace, or append to the section",
        min_length=1,
        max_length=50000
    )],
    operation: Annotated[Literal["insert_after", "insert_before", "replace_section", "append_to_section", "edit_heading"], Field(
        description="How to edit the section: insert_after (add content after heading), insert_before (add before heading), replace_section (replace entire section), append_to_section (add to end of section), edit_heading (change just the heading text)",
        default="insert_after"
    )] = "insert_after",
    create_if_missing: Annotated[bool, Field(
        description="Create the section if it doesn't exist",
        default=False
    )] = False,
    ctx=None
):
    """
    Edit a specific section of a note identified by a markdown heading.
    
    This tool enables token-efficient editing by targeting specific sections
    instead of rewriting entire notes. It preserves frontmatter and handles
    various section editing operations.
    
    When to use:
    - Adding tasks to a specific section without rewriting the whole note
    - Updating status sections in project notes
    - Building up notes incrementally by section
    - Inserting content at precise locations
    - Changing section headings while preserving content
    
    When NOT to use:
    - Making changes across multiple sections (use update_note instead)
    - Replacing entire note content (use update_note instead)
    - Simple text replacements (use edit_note_content instead)
    
    Args:
        path: Path to the note to edit
        section_identifier: Markdown heading to find (case-insensitive)
        content: Content to insert, replace, or append
        operation: Type of edit operation to perform
        create_if_missing: Create section if it doesn't exist
        
    Returns:
        Edit status with section details and operation performed
    """
    try:
        return await edit_note_section(path, section_identifier, content, operation, create_if_missing, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to edit note section: {str(e)}")

@mcp.tool()
async def edit_note_content_tool(
    path: Annotated[str, Field(
        description="Path to the note to edit",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/Website.md", "Notes/Research.md"]
    )],
    search_text: Annotated[str, Field(
        description="Exact text to search for and replace",
        min_length=1,
        max_length=10000
    )],
    replacement_text: Annotated[str, Field(
        description="Text to replace the search_text with",
        max_length=10000
    )],
    occurrence: Annotated[Literal["first", "all"], Field(
        description="Replace 'first' occurrence only or 'all' occurrences",
        default="first"
    )] = "first",
    ctx=None
):
    """
    Edit specific text content in a note using precise search and replace.
    
    This tool enables token-efficient editing by replacing specific text
    without rewriting entire notes. It's ideal for updating values, fixing
    typos, or making targeted changes to any part of the note.
    
    When to use:
    - Updating specific values or references
    - Fixing typos or correcting text
    - Modifying frontmatter properties
    - Changing URLs or links
    - Updating dates or numbers
    
    When NOT to use:
    - Making structural changes to sections (use edit_note_section instead)
    - Adding large blocks of content (use edit_note_section or update_note)
    - When exact text match is uncertain (read note first to verify)
    
    Args:
        path: Path to the note to edit
        search_text: Exact text to find
        replacement_text: Text to replace with
        occurrence: Replace first or all occurrences
        
    Returns:
        Edit status with replacement details
    """
    try:
        return await edit_note_content(path, search_text, replacement_text, occurrence, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to edit note content: {str(e)}")

@mcp.tool()
async def search_notes_tool(
    query: Annotated[str, Field(
        description="Search query with boolean operators (AND, OR, NOT) for fast full-text search. Also supports special prefixes like 'tag:' and 'path:' for filtered searches.",
        min_length=1,
        max_length=1000,
        examples=[
            "machine learning",
            "python AND tutorial", 
            "Eide Bailly OR CPA OR accounting",
            "(project OR task) NOT completed",
            "tag:project",
            "path:Daily/"
        ]
    )],
    max_results: Annotated[int, Field(
        description="Maximum number of results to return",
        default=50,
        ge=1,
        le=500
    )] = 50,
    context_length: Annotated[int, Field(
        description="Number of characters to show around matches",
        default=100,
        ge=50,
        le=500
    )] = 100,
    ctx=None
):
    """
    Lightning-fast full-text search using SQLite FTS5 indexing with boolean operators.
    
    This tool provides dramatically faster search performance compared to previous implementations,
    especially for large vaults (500+ notes). Supports advanced boolean queries and special search prefixes.
    
    Performance Benefits:
    - 100-1000x faster than legacy search on large vaults
    - Proper relevance ranking with FTS5
    - Boolean operator support (AND, OR, NOT)
    - Phrase search with quotes
    - Automatic index building and maintenance
    
    Search Syntax:
    - Simple search: "machine learning" (phrase search)
    - Boolean AND: "python AND tutorial" 
    - Boolean OR: "python OR javascript"
    - Boolean NOT: "python NOT snake"
    - Exact phrase: "machine learning algorithms"
    - Complex: "(python OR ruby) AND tutorial"
    - Tag search: "tag:project" (finds notes with #project tag)
    - Path search: "path:Daily/" (finds notes in Daily folder)
    
    When to use:
    - Finding notes by content keywords with advanced boolean logic
    - Complex queries with multiple terms and operators
    - Searching large vaults where speed is important
    - When you need properly ranked results
    
    When NOT to use:
    - Simple property searches (use search_by_property instead)
    - Date-based searches (use search_by_date instead)
    - Regex pattern matching (use search_by_regex instead)
    
    First-time usage: The search index is built automatically on first search,
    which may take 1-3 minutes for large vaults but dramatically speeds up all subsequent searches.
    
    Returns:
        Fast search results with matched notes, relevance scores, and highlighted context
    """
    try:
        return await search_notes(query, max_results, context_length, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Fast search failed: {str(e)}")

@mcp.tool()
async def search_by_date_tool(
    date_type: Annotated[Literal["created", "modified"], Field(
        description="Which date to search by: when the note was first created or last modified",
        default="modified"
    )] = "modified",
    days_ago: Annotated[int, Field(
        description="How many days back to search from today. 0 = today, 1 = yesterday, 7 = last week",
        ge=0,
        le=365,
        default=7,
        examples=[0, 1, 7, 30]
    )] = 7,
    operator: Annotated[Literal["within", "exactly"], Field(
        description="'within' = all notes in the last N days, 'exactly' = only notes from exactly N days ago",
        default="within"
    )] = "within",
    ctx=None
):
    """
    Search for notes by creation or modification date.
    
    When to use:
    - Finding recently modified notes
    - Locating notes created in a specific time period
    - Reviewing activity from specific dates
    
    When NOT to use:
    - Content-based search (use search_notes)
    - Finding notes by tags or path (use search_notes)
    
    Returns:
        Notes matching the date criteria with paths and timestamps
    """
    try:
        return await search_by_date(date_type, days_ago, operator, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Date search failed: {str(e)}")

@mcp.tool()
async def search_by_regex_tool(
    pattern: Annotated[str, Field(
        description="Regular expression pattern for advanced searches. Use for finding URLs, code patterns, TODO items, etc.",
        min_length=1,
        examples=[r"TODO\s*:.*", r"https?://[^\s]+", r"def\s+\w+\("]
    )],
    directory: Annotated[Optional[str], Field(
        description="Limit search to specific directory for DRAMATICALLY better performance. STRONGLY RECOMMENDED for vaults with 1000+ notes. Example: 'Projects' searches only the Projects folder instead of entire vault.",
        default=None,
        examples=["Projects", "Daily", "Archive/2024", "Work/Meetings"]
    )] = None,
    flags: Annotated[Optional[List[Literal["ignorecase", "multiline", "dotall"]]], Field(
        description="Options for regex matching: 'ignorecase' = case-insensitive, 'multiline' = ^ and $ match line boundaries, 'dotall' = . matches newlines",
        default=None
    )] = None,
    context_length: Annotated[int, Field(
        description="Characters to show around matches",
        default=100,
        ge=10,
        le=500
    )] = 100,
    max_results: Annotated[int, Field(
        description="Maximum number of notes to return. Use smaller values for faster responses.",
        default=50,
        ge=1,
        le=200
    )] = 50,
    ctx=None
):
    """
    Search for notes using regular expressions for advanced pattern matching with directory scoping.
    
    PERFORMANCE TIP: Use the 'directory' parameter to limit search scope for much faster results on large vaults.
    Instead of searching 1800+ files, search just 50-100 files in a specific folder.
    
    When to use:
    - Finding complex patterns (URLs, code syntax, structured data)
    - Searching with wildcards and special characters
    - Case-sensitive or multi-line pattern matching
    - Finding TODO/FIXME comments with context
    
    When NOT to use:
    - Simple text search (use search_notes with boolean operators instead)
    - Searching by tags or properties (use dedicated tools)
    
    Performance optimization:
    - ALWAYS use 'directory' parameter for large vaults (1000+ notes)
    - Example: directory="Projects" limits search to Projects folder only
    - This can make regex search 10-50x faster on large vaults
    
    Common patterns:
    - URLs: r"https?://[^\\s]+"
    - Email: r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    - TODO comments: r"(TODO|FIXME)\\s*:.*"
    - Markdown headers: r"^#{1,6}\\s+.*"
    - Code blocks: r"```\\w*\\n[\\s\\S]*?```"
    
    Returns:
        Notes containing regex matches with match details and context
    """
    try:
        return await search_by_regex(pattern, directory, flags, context_length, max_results, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Regex search failed: {str(e)}")

@mcp.tool()
async def search_by_property_tool(
    property_name: Annotated[str, Field(
        description="The frontmatter property to search for (e.g., 'status', 'priority'). These are metadata fields at the top of notes.",
        min_length=1,
        examples=["status", "priority", "author", "tags", "deadline"]
    )],
    value: Annotated[Optional[str], Field(
        description="The value to match against. Not needed when using 'exists' to just check if property is present.",
        default=None,
        examples=["active", "high", "2024-01-15", "John Doe"]
    )] = None,
    operator: Annotated[Literal["=", "!=", ">", "<", ">=", "<=", "contains", "exists"], Field(
        description="How to compare: '=' exact match, '!=' not equal, '>/</>=/<=' for numbers/dates, 'contains' partial match, 'exists' just checks presence",
        default="="
    )] = "=",
    context_length: Annotated[int, Field(
        description="Characters of note content to include",
        default=100,
        ge=0,
        le=500
    )] = 100,
    ctx=None
):
    """
    Search for notes by their frontmatter property values.
    
    When to use:
    - Finding notes with specific metadata (status, priority, etc.)
    - Filtering by numeric properties (rating > 4, priority <= 2)
    - Filtering by date properties (deadline < "2024-12-31")
    - Searching within array/list properties (tags, aliases, categories)
    - Checking which notes have certain properties defined
    - Building database-like queries on your notes
    
    Property types supported:
    - Text/String: Exact match or contains
    - Numbers: Comparison operators work numerically
    - Dates: ISO format (YYYY-MM-DD) with intelligent comparison
    - Arrays/Lists: Searches within list items, comparisons use list length
    - Legacy properties: Automatically handles tag→tags, alias→aliases migrations
    
    When NOT to use:
    - Content search (use search_notes instead)
    - Tag search (use search_notes with tag: prefix)
    - Path/filename search (use search_notes with path: prefix)
    
    Examples:
    - Find active projects: property_name="status", value="active"
    - Find high priority: property_name="priority", operator=">", value="2"
    - Find notes with deadlines: property_name="deadline", operator="exists"
    - Find notes by author: property_name="author", operator="contains", value="john"
    - Find notes with tag in list: property_name="tags", value="project"
    - Find past deadlines: property_name="due_date", operator="<", value="2024-01-01"
    
    Returns:
        Notes matching the property criteria with values displayed
    """
    try:
        return await search_by_property(property_name, value, operator, context_length, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Property search failed: {str(e)}")

@mcp.tool()
async def list_notes_tool(directory: str = None, recursive: bool = True, ctx=None):
    """
    List notes in the vault or a specific directory.
    
    Args:
        directory: Specific directory to list (optional, defaults to root)
        recursive: Whether to list all subdirectories recursively (default: true)
        
    Returns:
        Vault structure and note paths
    """
    try:
        return await list_notes(directory, recursive, ctx)
    except Exception as e:
        raise ToolError(f"Failed to list notes: {str(e)}")

@mcp.tool()
async def list_folders_tool(
    directory: Annotated[Optional[str], Field(
        description="Specific directory to list folders from (optional, defaults to root)",
        default=None,
        examples=[None, "Projects", "Daily", "Archive/2024"]
    )] = None,
    recursive: Annotated[bool, Field(
        description="Whether to include all nested subfolders",
        default=True
    )] = True,
    ctx=None
):
    """
    List folders in the vault or a specific directory.
    
    When to use:
    - Exploring vault organization structure
    - Verifying folder names before creating notes
    - Checking if a specific folder exists
    - Understanding the hierarchy of the vault
    
    When NOT to use:
    - Listing notes (use list_notes instead)
    - Searching for content (use search_notes)
    
    Returns:
        Folder structure with paths and names
    """
    try:
        return await list_folders(directory, recursive, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to list folders: {str(e)}")

@mcp.tool()
async def move_note_tool(source_path: str, destination_path: str, update_links: bool = True, ctx=None):
    """
    Move a note to a new location, optionally updating all links.
    
    Args:
        source_path: Current path of the note
        destination_path: New path for the note
        update_links: Whether to update links in other notes (default: true)
        
    Returns:
        Move status and updated links count
    """
    try:
        return await move_note(source_path, destination_path, update_links, ctx)
    except (ValueError, FileNotFoundError, FileExistsError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to move note: {str(e)}")

@mcp.tool()
async def create_folder_tool(
    folder_path: Annotated[str, Field(
        description="Path of the folder to create",
        min_length=1,
        max_length=255,
        examples=["Projects/2025", "Archive/Q1", "Daily/January"]
    )],
    create_placeholder: Annotated[bool, Field(
        description="Whether to create a placeholder file (.gitkeep or README.md)",
        default=True
    )] = True,
    ctx=None
):
    """
    Create a new folder in the vault, including all parent folders in the path.
    
    When to use:
    - Setting up project structure in advance
    - Creating deep folder hierarchies (e.g., "Research/Studies/2024")
    - Creating archive folders before moving notes
    - Establishing organizational hierarchy
    - Preparing folders for future content
    
    When NOT to use:
    - If you're about to create a note in that path (folders are created automatically)
    - For temporary organization (just create notes directly)
    
    Note: Will create all necessary parent folders. For example, "Research/Studies/2024"
    will create Research, Research/Studies, and Research/Studies/2024 if they don't exist.
    
    Returns:
        Creation status with list of folders created and placeholder file path
    """
    try:
        return await create_folder(folder_path, create_placeholder, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to create folder: {str(e)}")

@mcp.tool()
async def move_folder_tool(
    source_folder: Annotated[str, Field(
        description="Current folder path to move",
        min_length=1,
        max_length=255,
        examples=["Projects/Old", "Archive/2023", "Inbox/Unsorted"]
    )],
    destination_folder: Annotated[str, Field(
        description="New location for the folder",
        min_length=1,
        max_length=255,
        examples=["Archive/Projects/Old", "Completed/2023", "Projects/Sorted"]
    )],
    update_links: Annotated[bool, Field(
        description="Whether to update links in other notes (future enhancement)",
        default=True
    )] = True,
    ctx=None
):
    """
    Move an entire folder and all its contents to a new location.
    
    When to use:
    - Reorganizing vault structure
    - Archiving completed projects
    - Consolidating related notes
    - Seasonal organization (e.g., moving to year-based archives)
    
    When NOT to use:
    - Moving individual notes (use move_note instead)
    - Moving to a subfolder of the source (creates circular reference)
    
    Returns:
        Move status with count of notes and folders moved
    """
    try:
        return await move_folder(source_folder, destination_folder, update_links, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to move folder: {str(e)}")

@mcp.tool()
async def add_tags_tool(
    path: Annotated[str, Field(
        description="Path to the note",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    tags: Annotated[List[str], Field(
        description="List of tags to add to the note. Don't include the # symbol - it will be added automatically. Supports hierarchical tags with forward slashes.",
        min_length=1,
        max_length=50,
        examples=[["project", "urgent"], ["project/web", "project/mobile"], ["work/meetings/standup", "work/meetings/planning"]]
    )],
    ctx=None
):
    """
    Add tags to a note's frontmatter.
    
    When to use:
    - Organizing notes with tags
    - Creating hierarchical tag structures (e.g., project/web, work/meetings/standup)
    - Bulk tagging operations
    - Adding metadata for search
    
    Tag format:
    - Simple tags: "project", "urgent"
    - Hierarchical tags: "project/web", "work/meetings/standup"
    - Tags are automatically added without duplicates
    
    When NOT to use:
    - Adding tags in note content (use update_note)
    - Replacing all tags (use update_tags with merge=False)
    
    Returns:
        Updated tag list for the note
    """
    try:
        return await add_tags(path, tags, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to add tags: {str(e)}")

@mcp.tool()
async def update_tags_tool(
    path: Annotated[str, Field(
        description="Path to the note",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    tags: Annotated[List[str], Field(
        description="New tags for the note. Empty list removes all tags. Don't include # symbols. Supports hierarchical tags with forward slashes.",
        min_length=0,
        max_length=50,
        examples=[["meeting", "important", "q1-2025"], ["project/ai", "research/neural-networks", "status/active"]]
    )],
    merge: Annotated[bool, Field(
        description="True = add these tags to existing ones, False = replace all tags with this new list",
        default=False
    )] = False,
    ctx=None
):
    """
    Update tags on a note - either replace all tags or merge with existing.
    
    When to use:
    - After analyzing a note's content to suggest relevant tags
    - Reorganizing tags across your vault
    - Setting consistent tags based on note types or projects
    - AI-driven tag suggestions ("What is this note about? Add appropriate tags")
    
    When NOT to use:
    - Just adding a few tags (use add_tags)
    - Just removing specific tags (use remove_tags)
    
    Returns:
        Previous tags, new tags, and operation performed
    """
    try:
        return await update_tags(path, tags, merge, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to update tags: {str(e)}")

@mcp.tool()
async def remove_tags_tool(path: str, tags: list[str], ctx=None):
    """
    Remove tags from a note's frontmatter.
    
    Args:
        path: Path to the note
        tags: List of tags to remove (without # prefix)
        
    Returns:
        Updated tag list
    """
    try:
        return await remove_tags(path, tags, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to remove tags: {str(e)}")

@mcp.tool()
async def get_note_info_tool(path: str, ctx=None):
    """
    Get metadata and information about a note without retrieving its full content.
    
    Args:
        path: Path to the note
        
    Returns:
        Note metadata and statistics
    """
    try:
        return await get_note_info(path, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to get note info: {str(e)}")

@mcp.tool()
async def get_backlinks_tool(
    path: Annotated[str, Field(
        description="Path to the note to find backlinks for",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/AI Research.md"]
    )],
    include_context: Annotated[bool, Field(
        description="Include the text surrounding each link to understand why the link was made",
        default=True
    )] = True,
    context_length: Annotated[int, Field(
        description="How much surrounding text to show for each link (in characters)",
        ge=50,
        le=500,
        default=100
    )] = 100,
    ctx=None
):
    """
    Find all notes that link to a specific note (backlinks).
    
    When to use:
    - Understanding which notes reference a concept or topic
    - Discovering relationships between notes
    - Finding notes that depend on the current note
    - Building a mental map of note connections
    
    When NOT to use:
    - Finding links FROM a note (use get_outgoing_links)
    - Searching for broken links (use find_broken_links)
    
    Performance note:
    - Fast for small vaults (<100 notes)
    - May take several seconds for large vaults (1000+ notes)
    - Consider using search_notes for specific link queries
    
    Returns:
        All notes linking to the target with optional context
    """
    try:
        return await get_backlinks(path, include_context, context_length, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to get backlinks: {str(e)}")

@mcp.tool()
async def get_outgoing_links_tool(
    path: Annotated[str, Field(
        description="Path to the note to extract links from",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Projects/Overview.md", "Index.md"]
    )],
    check_validity: Annotated[bool, Field(
        description="Also check if each linked note actually exists in your vault",
        default=False
    )] = False,
    ctx=None
):
    """
    List all links from a specific note (outgoing links).
    
    When to use:
    - Understanding what a note references
    - Checking note dependencies before moving/deleting
    - Exploring the structure of index or hub notes
    - Validating links after changes
    
    When NOT to use:
    - Finding notes that link TO this note (use get_backlinks)
    - Searching across multiple notes (use find_broken_links)
    
    Returns:
        All outgoing links with their types and optional validity status
    """
    try:
        return await get_outgoing_links(path, check_validity, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to get outgoing links: {str(e)}")

@mcp.tool()
async def find_broken_links_tool(
    directory: Annotated[Optional[str], Field(
        description="Check only this folder and its subfolders. Leave empty to check entire vault.",
        default=None,
        examples=[None, "Projects", "Archive/2023"]
    )] = None,
    single_note: Annotated[Optional[str], Field(
        description="Check links in just this one note instead of the whole vault or directory",
        default=None,
        examples=["Daily/2025-01-09.md", "Projects/Overview.md"]
    )] = None,
    ctx=None
):
    """
    Find all broken links in the vault, a specific directory, or a single note.
    
    When to use:
    - After renaming or deleting notes
    - Regular vault maintenance
    - Before reorganizing folder structure
    - Cleaning up after imports
    - Checking links in a specific note
    
    When NOT to use:
    - Just getting outgoing links without needing broken status (use get_outgoing_links)
    - Finding backlinks (use get_backlinks)
    
    Returns:
        All broken links found in the specified scope
    """
    try:
        return await find_broken_links(directory, single_note, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to find broken links: {str(e)}")

@mcp.tool()
async def list_tags_tool(
    include_counts: Annotated[bool, Field(
        description="Show how many times each tag is used across your vault",
        default=True
    )] = True,
    sort_by: Annotated[Literal["name", "count"], Field(
        description="Sort tags alphabetically by 'name' or by popularity with 'count'",
        default="name"
    )] = "name",
    ctx=None
):
    """
    List all unique tags used across the vault with usage statistics.
    
    When to use:
    - Before adding tags to maintain consistency
    - Getting an overview of your tagging taxonomy
    - Finding underused or overused tags
    - Discovering tag variations (e.g., 'project' vs 'projects')
    - Understanding hierarchical tag structures in your vault
    
    Hierarchical tags:
    - Lists both parent and full hierarchical paths (e.g., both "project" and "project/web")
    - Shows how nested tags are organized in your vault
    - Helps identify opportunities for better tag organization
    
    When NOT to use:
    - Getting tags for a specific note (use get_note_info)
    - Searching notes by tag (use search_notes with tag: prefix)
    
    Performance note:
    - For vaults with <1000 notes: Fast (1-3 seconds)
    - For vaults with 1000-5000 notes: Moderate (3-10 seconds)
    - For vaults with >5000 notes: May be slow (10+ seconds)
    - Uses batched concurrent requests to optimize performance
    
    Returns:
        All unique tags with optional usage counts
    """
    try:
        return await list_tags(include_counts, sort_by, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to list tags: {str(e)}")

@mcp.tool()
async def read_image_tool(
    path: Annotated[str, Field(
        description="Path to the image file relative to vault root",
        pattern=r"^[^/].*\.(png|jpg|jpeg|gif|webp|svg|bmp|ico)$",
        min_length=1,
        max_length=255,
        examples=["attachments/screenshot.png", "images/diagram.jpg", "media/logo.svg"]
    )],
    include_metadata: Annotated[bool, Field(
        description="Include file size and other metadata about the image",
        default=False
    )] = False,
    ctx=None
):
    """
    Read an image file from the Obsidian vault for analysis.
    
    When to use:
    - Analyzing specific image files from the vault
    - Examining standalone images (not embedded in notes)
    - Processing images for detailed analysis
    
    When NOT to use:
    - Getting images embedded in notes (use view_note_images instead)
    - Searching for images (use list_notes with appropriate filters)
    
    Returns:
        Image object that Claude can analyze and describe
    """
    try:
        return await read_image(path, include_metadata, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to read image: {str(e)}")

@mcp.tool()
async def view_note_images_tool(
    path: Annotated[str, Field(
        description="Path to the note containing images",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Projects/Design.md", "Daily/2024-01-15.md", "Ideas/Mockups.md"]
    )],
    image_index: Annotated[Optional[int], Field(
        description="Get only the Nth image from the note (0 = first image). Leave empty to get all images.",
        default=None,
        ge=0
    )] = None,
    max_width: Annotated[int, Field(
        description="Resize images wider than this to save memory. Images smaller than this are unchanged.",
        default=1600,
        gt=0,
        le=4096
    )] = 800,
    ctx=None
):
    """
    Extract and analyze images embedded in a note.
    
    When to use:
    - Analyzing images referenced in a note's markdown content
    - Examining visual content within notes (screenshots, diagrams, etc.)
    - Extracting specific images from notes for analysis
    
    When NOT to use:
    - Reading standalone image files (use read_image instead)
    - Getting note content without images (use read_note instead)
    
    Returns:
        List of Image objects that Claude can analyze and describe
    """
    try:
        return await view_note_images(path, image_index, max_width, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Failed to view note images: {str(e)}")


# === FAST SEARCH TOOLS (FTS5) ===

@mcp.tool()
async def search_by_field_tool(
    field: Annotated[Literal["filename", "tags", "properties", "content"], Field(
        description="Field to search within",
        examples=["filename", "tags", "properties", "content"]
    )],
    value: Annotated[str, Field(
        description="Value to search for in the specified field",
        min_length=1,
        max_length=500,
        examples=["README", "project", "status:active", "tutorial"]
    )],
    max_results: Annotated[int, Field(
        description="Maximum number of results to return",
        default=50,
        ge=1,
        le=200
    )] = 50,
    ctx=None
):
    """
    Search within specific fields like filename, tags, or properties using fast FTS5.
    
    This tool allows targeted searching within specific parts of your notes
    for more precise results when you know which field contains your target.
    
    Supported Fields:
    - filename: Search note titles/filenames only
    - tags: Search note tags only  
    - properties: Search frontmatter properties only
    - content: Search note content (same as search_notes)
    
    When to use:
    - Searching for specific filenames or titles
    - Finding notes with specific tags
    - Locating notes with certain property values
    - When you want field-specific rather than full-text search
    
    When NOT to use:
    - General content search (use search_notes instead)
    - Multiple field search (use search_notes with boolean operators)
    """
    try:
        return await search_by_field(field, value, max_results, ctx)
    except ValueError as e:
        raise ToolError(str(e))
    except Exception as e:
        raise ToolError(f"Field search failed: {str(e)}")


@mcp.tool()
async def rebuild_search_index_tool(ctx=None):
    """
    Rebuild the fast search index from scratch.
    
    This tool rebuilds the FTS5 search index by scanning all notes in your vault.
    Use this when search results seem outdated or when using fast search for the first time.
    
    When to use:
    - First time using search tools
    - Search results seem outdated or incomplete
    - After making major changes to your vault structure
    - If search is returning errors
    - To ensure the index includes all recent notes
    
    When NOT to use:
    - For routine searches (index is updated automatically)
    - If the index is already fresh and working well
    
    Note: This may take 1-3 minutes for large vaults (1000+ notes) but dramatically
    improves search performance afterward.
    """
    try:
        return await rebuild_search_index(ctx)
    except Exception as e:
        raise ToolError(f"Failed to rebuild search index: {str(e)}")


@mcp.tool()
async def get_search_stats_tool(ctx=None):
    """
    Get statistics about the fast search index status and performance.
    
    Provides information about the current state of the FTS5 search index
    including how many files are indexed, index freshness, and recommendations.
    
    When to use:
    - Checking if the search index is ready
    - Diagnosing search performance issues
    - Understanding search index status
    - Before deciding whether to rebuild the index
    
    Returns information about:
    - Number of indexed files
    - Total content size indexed
    - Index age/freshness
    - Performance recommendations
    """
    try:
        return await get_search_stats(ctx)
    except Exception as e:
        raise ToolError(f"Failed to get search stats: {str(e)}")


def main():
    """Entry point for packaged distribution."""
    mcp.run()


if __name__ == "__main__":
    main()