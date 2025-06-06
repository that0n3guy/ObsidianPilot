"""Note management tools for Obsidian MCP server."""

from typing import Optional
from fastmcp import Context
from ..utils import ObsidianAPI, validate_note_path, sanitize_path
from ..utils.validation import validate_content
from ..models import Note
from ..constants import ERROR_MESSAGES


async def read_note(path: str, ctx: Optional[Context] = None) -> dict:
    """
    Read the content and metadata of a specific note.
    
    Use this tool when you need to retrieve the full content of a note
    from the Obsidian vault. The path should be relative to the vault root.
    
    Args:
        path: Path to the note relative to vault root (e.g., "Daily/2024-01-15.md")
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing the note content and metadata
        
    Example:
        >>> await read_note("Projects/My Project.md", ctx)
        {
            "path": "Projects/My Project.md",
            "content": "# My Project\n\nProject details...",
            "metadata": {
                "tags": ["project", "active"],
                "created": "2024-01-15T10:00:00Z",
                "modified": "2024-01-15T14:30:00Z"
            }
        }
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    # Sanitize path
    path = sanitize_path(path)
    
    if ctx:
        ctx.info(f"Reading note: {path}")
    
    api = ObsidianAPI()
    note = await api.get_note(path)
    
    if not note:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    return {
        "path": note.path,
        "content": note.content,
        "metadata": note.metadata.model_dump(exclude_none=True)
    }


async def create_note(
    path: str, 
    content: str, 
    overwrite: bool = False,
    ctx: Optional[Context] = None
) -> dict:
    """
    Create a new note or update an existing one.
    
    Use this tool to create new notes in the Obsidian vault. By default,
    it will fail if a note already exists at the specified path unless
    overwrite is set to true.
    
    Args:
        path: Path where the note should be created (e.g., "Ideas/New Idea.md")
        content: Markdown content for the note
        overwrite: Whether to overwrite if the note already exists (default: false)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing the created note information
        
    Example:
        >>> await create_note(
        ...     "Ideas/AI Integration.md",
        ...     "# AI Integration Ideas\n\n- Use LLMs for note summarization\n- Auto-tagging",
        ...     ctx=ctx
        ... )
        {
            "path": "Ideas/AI Integration.md",
            "created": true,
            "metadata": {"tags": [], "created": "2024-01-15T15:00:00Z"}
        }
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    # Validate content
    is_valid, error_msg = validate_content(content)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Sanitize path
    path = sanitize_path(path)
    
    if ctx:
        ctx.info(f"Creating note: {path}")
    
    api = ObsidianAPI()
    
    # Check if note exists
    existing_note = await api.get_note(path)
    if existing_note and not overwrite:
        raise FileExistsError(ERROR_MESSAGES["overwrite_protection"].format(path=path))
    
    # Create or update the note
    note = await api.create_note(path, content)
    
    return {
        "path": note.path,
        "created": existing_note is None,
        "metadata": note.metadata.model_dump(exclude_none=True)
    }


async def update_note(
    path: str,
    content: str,
    create_if_not_exists: bool = False,
    merge_strategy: str = "replace",
    ctx: Optional[Context] = None
) -> dict:
    """
    Update the content of an existing note.
    
    Use this tool to modify the content of an existing note while preserving
    its metadata and location. Optionally create the note if it doesn't exist.
    
    IMPORTANT: This tool REPLACES the entire note content by default. Always
    read the note first with read_note_tool if you want to preserve existing content.
    
    Args:
        path: Path to the note to update
        content: New markdown content for the note (REPLACES existing content)
        create_if_not_exists: Create the note if it doesn't exist (default: false)
        merge_strategy: How to handle updates - "replace" (default) or "append"
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing update status
        
    Example:
        >>> await update_note(
        ...     "Projects/My Project.md",
        ...     "# My Project\\n\\n## Updated Status\\nProject is now complete!",
        ...     ctx=ctx
        ... )
        {
            "path": "Projects/My Project.md",
            "updated": true,
            "created": false,
            "metadata": {"tags": ["project", "completed"], "modified": "2024-01-15T16:00:00Z"}
        }
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    # Sanitize path
    path = sanitize_path(path)
    
    if ctx:
        ctx.info(f"Updating note: {path}")
    
    api = ObsidianAPI()
    
    # Check if note exists
    existing_note = await api.get_note(path)
    
    if not existing_note:
        if create_if_not_exists:
            # Create the note
            note = await api.create_note(path, content)
            return {
                "path": note.path,
                "updated": False,
                "created": True,
                "metadata": note.metadata.model_dump(exclude_none=True)
            }
        else:
            raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Handle merge strategies
    if merge_strategy == "append":
        # Append to existing content
        final_content = existing_note.content.rstrip() + "\n\n" + content
    elif merge_strategy == "replace":
        # Replace entire content (default)
        final_content = content
    else:
        raise ValueError(f"Invalid merge_strategy: {merge_strategy}. Must be 'replace' or 'append'")
    
    # Update existing note
    note = await api.update_note(path, final_content)
    
    return {
        "path": note.path,
        "updated": True,
        "created": False,
        "metadata": note.metadata.model_dump(exclude_none=True),
        "merge_strategy": merge_strategy
    }


async def delete_note(path: str, ctx: Optional[Context] = None) -> dict:
    """
    Delete a note from the vault.
    
    Use this tool to permanently remove a note from the Obsidian vault.
    This action cannot be undone.
    
    Args:
        path: Path to the note to delete
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing deletion status
        
    Example:
        >>> await delete_note("Temporary/Draft.md", ctx)
        {"path": "Temporary/Draft.md", "deleted": true}
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    # Sanitize path
    path = sanitize_path(path)
    
    if ctx:
        ctx.info(f"Deleting note: {path}")
    
    api = ObsidianAPI()
    deleted = await api.delete_note(path)
    
    if not deleted:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    return {
        "path": path,
        "deleted": True
    }