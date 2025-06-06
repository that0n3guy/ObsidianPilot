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
    move_note,
    add_tags,
    remove_tags,
    get_note_info,
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
    - Verifying a note exists before updating
    
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
async def create_note_tool(path: str, content: str, overwrite: bool = False, ctx=None):
    """
    Create a new note or update an existing one.
    
    Args:
        path: Path where the note should be created (e.g., "Ideas/New Idea.md")
        content: Markdown content for the note
        overwrite: Whether to overwrite if the note already exists (default: false)
        
    Returns:
        Created note information
    """
    try:
        return await create_note(path, content, overwrite, ctx)
    except (ValueError, FileExistsError) as e:
        raise McpError(str(e))
    except Exception as e:
        raise McpError(f"Failed to create note: {str(e)}")

@mcp.tool()
async def update_note_tool(path: str, content: str, create_if_not_exists: bool = False, ctx=None):
    """
    Update the content of an existing note.
    
    Args:
        path: Path to the note to update
        content: New markdown content for the note
        create_if_not_exists: Create the note if it doesn't exist (default: false)
        
    Returns:
        Update status
    """
    try:
        return await update_note(path, content, create_if_not_exists, ctx)
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


if __name__ == "__main__":
    mcp.run()