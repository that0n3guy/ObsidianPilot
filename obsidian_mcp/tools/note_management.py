"""Note management tools for Obsidian MCP server."""

import asyncio
import re
from typing import Optional, List, Dict, Any
from fastmcp import Context
from ..utils.filesystem import get_vault
from ..utils import validate_note_path, sanitize_path
from ..utils.validation import validate_content
from ..models import Note
from ..constants import ERROR_MESSAGES


async def read_note(
    path: str, 
    ctx: Optional[Context] = None
) -> dict:
    """
    Read the content and metadata of a specific note.
    
    Use this tool when you need to retrieve the full content of a note
    from the Obsidian vault. The path should be relative to the vault root.
    
    To view images embedded in a note, use the view_note_images tool.
    
    Args:
        path: Path to the note relative to vault root (e.g., "Daily/2024-01-15.md")
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing the note content and metadata
        
    Example:
        >>> await read_note("Projects/My Project.md", ctx=ctx)
        {
            "path": "Projects/My Project.md",
            "content": "# My Project\n\n![diagram](attachments/diagram.png)\n\nProject details...",
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
    
    vault = get_vault()
    try:
        note = await vault.read_note(path)
    except FileNotFoundError:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Return standardized CRUD success structure
    return {
        "success": True,
        "path": note.path,
        "operation": "read",
        "details": {
            "content": note.content,
            "metadata": note.metadata.model_dump(exclude_none=True)
        }
    }


async def _search_and_load_image(
    image_ref: str,
    vault,
    ctx: Optional[Context] = None
) -> Optional[Dict[str, Any]]:
    """
    Search for and load a single image.
    
    Args:
        image_ref: Image reference (path or filename)
        vault: ObsidianVault instance
        ctx: Optional context for logging
        
    Returns:
        Image data dict or None if not found
    """
    try:
        if ctx:
            ctx.info(f"Loading embedded image: {image_ref}")
        
        # Try to read the image directly (with resizing for embedded images)
        try:
            image_data = await vault.read_image(image_ref, max_width=800)
        except FileNotFoundError:
            # If not found at direct path, search for it
            if ctx:
                ctx.info(f"Image not found at direct path, searching for: {image_ref}")
            
            # Extract just the filename
            filename = image_ref.split('/')[-1]
            
            # Use vault's find_image method
            found_path = await vault.find_image(filename)
            if found_path:
                if ctx:
                    ctx.info(f"Found image at: {found_path}")
                image_data = await vault.read_image(found_path, max_width=800)
            else:
                image_data = None
        
        if image_data:
            return {
                "path": image_data["path"],
                "content": image_data["content"],
                "mime_type": image_data["mime_type"]
            }
        elif ctx:
            ctx.info(f"Could not find image anywhere: {image_ref}")
            
    except Exception as e:
        # Log error but return None
        if ctx:
            ctx.info(f"Failed to load image {image_ref}: {str(e)}")
    
    return None


async def _extract_and_load_images(
    content: str, 
    vault,
    ctx: Optional[Context] = None
) -> List[Dict[str, Any]]:
    """
    Extract image references from markdown content and load them concurrently.
    
    Supports both Obsidian wiki-style (![[image.png]]) and standard markdown (![alt](image.png)) formats.
    """
    # Pattern for wiki-style embeds: ![[image.png]]
    wiki_pattern = r'!\[\[([^]]+\.(?:png|jpg|jpeg|gif|webp|svg|bmp|ico))\]\]'
    # Pattern for standard markdown: ![alt text](image.png)
    markdown_pattern = r'!\[[^\]]*\]\(([^)]+\.(?:png|jpg|jpeg|gif|webp|svg|bmp|ico))\)'
    
    # Find all image references
    image_paths = set()
    
    for match in re.finditer(wiki_pattern, content, re.IGNORECASE):
        image_paths.add(match.group(1))
    
    for match in re.finditer(markdown_pattern, content, re.IGNORECASE):
        image_paths.add(match.group(1))
    
    # Load all images concurrently for better performance
    if not image_paths:
        return []
    
    # Create tasks for all images
    tasks = [_search_and_load_image(image_ref, vault, ctx) for image_ref in image_paths]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None results and exceptions
    images = []
    for result in results:
        if result and not isinstance(result, Exception):
            images.append(result)
    
    return images


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
    
    vault = get_vault()
    
    # Create the note
    try:
        note = await vault.write_note(path, content, overwrite=overwrite)
        created = True
    except FileExistsError:
        if not overwrite:
            raise FileExistsError(ERROR_MESSAGES["overwrite_protection"].format(path=path))
        # If we get here, overwrite is True but file exists - this shouldn't happen
        # with our write_note implementation, but handle it just in case
        note = await vault.write_note(path, content, overwrite=True)
        created = False
    
    # Return standardized CRUD success structure
    return {
        "success": True,
        "path": note.path,
        "operation": "created" if created else "overwritten",
        "details": {
            "created": created,
            "overwritten": not created,
            "metadata": note.metadata.model_dump(exclude_none=True)
        }
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
    
    vault = get_vault()
    
    # Try to read existing note
    try:
        existing_note = await vault.read_note(path)
        note_exists = True
    except FileNotFoundError:
        note_exists = False
        existing_note = None
    
    if not note_exists:
        if create_if_not_exists:
            # Create the note
            note = await vault.write_note(path, content, overwrite=False)
            # Return standardized CRUD success structure
            return {
                "success": True,
                "path": note.path,
                "operation": "created",
                "details": {
                    "updated": False,
                    "created": True,
                    "metadata": note.metadata.model_dump(exclude_none=True)
                }
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
    note = await vault.write_note(path, final_content, overwrite=True)
    
    # Return standardized CRUD success structure
    return {
        "success": True,
        "path": note.path,
        "operation": "updated",
        "details": {
            "updated": True,
            "created": False,
            "merge_strategy": merge_strategy,
            "metadata": note.metadata.model_dump(exclude_none=True)
        }
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
    
    vault = get_vault()
    
    try:
        await vault.delete_note(path)
        deleted = True
    except FileNotFoundError:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Return standardized CRUD success structure
    return {
        "success": True,
        "path": path,
        "operation": "deleted",
        "details": {
            "deleted": True
        }
    }