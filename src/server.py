"""Main entry point for Obsidian MCP server."""

import os
from typing import Annotated, Optional, List, Literal
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import McpError

# Import all tools
from .tools import (
    read_note,
    create_note,
    update_note,
    delete_note,
    search_notes,
    search_by_date,
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
)

# Check for API key
if not os.getenv("OBSIDIAN_REST_API_KEY"):
    raise ValueError("OBSIDIAN_REST_API_KEY environment variable must be set")

# Create FastMCP server instance
mcp = FastMCP(
    "obsidian-mcp",
    description="MCP server for interacting with Obsidian vaults through the Local REST API"
)

# Register tools with proper error handling
@mcp.tool()
async def read_note_tool(
    path: Annotated[str, Field(
        description="Path to the note relative to vault root",
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
    
    Returns:
        Note content and metadata including tags, aliases, and frontmatter
    """
    try:
        return await read_note(path, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to read note: {str(e)}")

@mcp.tool()
async def create_note_tool(
    path: Annotated[str, Field(
        description="Path where the note should be created relative to vault root",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Ideas/New Idea.md", "Daily/2024-01-15.md", "Projects/Project Plan.md"]
    )],
    content: Annotated[str, Field(
        description="Markdown content for the note. Consider adding tags (use list_tags to see existing ones)",
        min_length=0,
        max_length=1000000,
        examples=[
            "# Meeting Notes\n#meeting #project-alpha\n\nDiscussed timeline and deliverables...",
            "---\ntags: [daily, planning]\n---\n\n# Daily Note\n\nToday's tasks..."
        ]
    )],
    overwrite: Annotated[bool, Field(
        description="Whether to overwrite if the note already exists",
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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to create note: {str(e)}")

@mcp.tool()
async def update_note_tool(
    path: Annotated[str, Field(
        description="Path to the note to update",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255,
        examples=["Daily/2024-01-15.md", "Projects/Project.md"]
    )],
    content: Annotated[str, Field(
        description="New markdown content (REPLACES existing content unless using append)",
        min_length=0,
        max_length=1000000
    )],
    create_if_not_exists: Annotated[bool, Field(
        description="Create the note if it doesn't exist",
        default=False
    )] = False,
    merge_strategy: Annotated[Literal["replace", "append"], Field(
        description="How to handle content: 'replace' overwrites, 'append' adds to end",
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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to update note: {str(e)}")

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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to delete note: {str(e)}")

@mcp.tool()
async def search_notes_tool(
    query: Annotated[str, Field(
        description="Search query supporting Obsidian syntax",
        min_length=1,
        max_length=500,
        examples=[
            "machine learning",
            "tag:#project",
            "path:Daily/",
            "tag:#urgent TODO"
        ]
    )],
    context_length: Annotated[int, Field(
        description="Number of characters to show around matches",
        ge=10,
        le=500,
        default=100
    )] = 100,
    ctx=None
):
    """
    Search for notes containing specific text or matching search criteria.
    
    When to use:
    - Finding notes by content keywords
    - Locating notes with specific tags
    - Searching within specific folders
    
    When NOT to use:
    - Searching by date (use search_by_date instead)
    - Listing all notes (use list_notes for better performance)
    - Finding a specific known note (use read_note directly)
    
    Returns:
        Search results with matched notes, relevance scores, and context
    """
    try:
        return await search_notes(query, context_length, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Search failed: {str(e)}")

@mcp.tool()
async def search_by_date_tool(
    date_type: Annotated[Literal["created", "modified"], Field(
        description="Type of date to search by",
        default="modified"
    )] = "modified",
    days_ago: Annotated[int, Field(
        description="Number of days to look back from today",
        ge=0,
        le=365,
        default=7,
        examples=[0, 1, 7, 30]
    )] = 7,
    operator: Annotated[Literal["within", "exactly"], Field(
        description="Search operator for date matching",
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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Date search failed: {str(e)}")

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
        raise McpError(f"Failed to list notes: {str(e)}")

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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to list folders: {str(e)}")

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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to move note: {str(e)}")

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
    - Creating deep folder hierarchies (e.g., "Apple/Studies/J71P")
    - Creating archive folders before moving notes
    - Establishing organizational hierarchy
    - Preparing folders for future content
    
    When NOT to use:
    - If you're about to create a note in that path (folders are created automatically)
    - For temporary organization (just create notes directly)
    
    Note: Will create all necessary parent folders. For example, "Apple/Studies/J71P"
    will create Apple, Apple/Studies, and Apple/Studies/J71P if they don't exist.
    
    Returns:
        Creation status with list of folders created and placeholder file path
    """
    try:
        return await create_folder(folder_path, create_placeholder, ctx)
    except ValueError as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to create folder: {str(e)}")

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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to move folder: {str(e)}")

@mcp.tool()
async def add_tags_tool(
    path: Annotated[str, Field(
        description="Path to the note",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    tags: Annotated[List[str], Field(
        description="Tags to add (without # prefix)",
        min_items=1,
        max_items=50,
        examples=[["project", "urgent"], ["meeting", "followup", "q1-2024"]]
    )],
    ctx=None
):
    """
    Add tags to a note's frontmatter.
    
    When to use:
    - Organizing notes with tags
    - Bulk tagging operations
    - Adding metadata for search
    
    When NOT to use:
    - Adding tags in note content (use update_note)
    - Replacing all tags (use update_note with new frontmatter)
    
    Returns:
        Updated tag list for the note
    """
    try:
        return await add_tags(path, tags, ctx)
    except (ValueError, FileNotFoundError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to add tags: {str(e)}")

@mcp.tool()
async def update_tags_tool(
    path: Annotated[str, Field(
        description="Path to the note",
        pattern=r"^[^/].*\.md$",
        min_length=1,
        max_length=255
    )],
    tags: Annotated[List[str], Field(
        description="New tags to set (without # prefix)",
        min_items=0,
        max_items=50,
        examples=[["meeting", "important", "q1-2025"], ["ai", "research", "neural-networks"]]
    )],
    merge: Annotated[bool, Field(
        description="If True, adds to existing tags. If False, replaces all tags",
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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to update tags: {str(e)}")

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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to remove tags: {str(e)}")

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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get note info: {str(e)}")

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
        description="Whether to include text context around links",
        default=True
    )] = True,
    context_length: Annotated[int, Field(
        description="Number of characters of context to include",
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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get backlinks: {str(e)}")

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
        description="Whether to check if linked notes exist",
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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to get outgoing links: {str(e)}")

@mcp.tool()
async def find_broken_links_tool(
    directory: Annotated[Optional[str], Field(
        description="Specific directory to check (optional, defaults to entire vault)",
        default=None,
        examples=[None, "Projects", "Archive/2023"]
    )] = None,
    single_note: Annotated[Optional[str], Field(
        description="Check only this specific note (optional)",
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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to find broken links: {str(e)}")

@mcp.tool()
async def list_tags_tool(
    include_counts: Annotated[bool, Field(
        description="Whether to include usage count for each tag",
        default=True
    )] = True,
    sort_by: Annotated[Literal["name", "count"], Field(
        description="How to sort results - by name (alphabetical) or count (usage)",
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
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to list tags: {str(e)}")




def main():
    """Entry point for packaged distribution."""
    mcp.run()


if __name__ == "__main__":
    main()