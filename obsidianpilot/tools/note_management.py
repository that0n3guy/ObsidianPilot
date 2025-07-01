"""Note management tools for Obsidian MCP server."""

import asyncio
import re
from typing import Optional, List, Dict, Any, Tuple, Literal
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
        
        # Update search index in background
        from ..utils.index_updater import update_index_for_file
        import asyncio
        asyncio.create_task(update_index_for_file(path))
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
            
            # Update search index in background
            from ..utils.index_updater import update_index_for_file
            import asyncio
            asyncio.create_task(update_index_for_file(path))
            
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
    
    # Update search index in background
    from ..utils.index_updater import update_index_for_file
    import asyncio
    asyncio.create_task(update_index_for_file(path))
    
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


# Helper functions for token-efficient editing

def _detect_frontmatter(content: str) -> Tuple[str, str, str]:
    """
    Detect and separate frontmatter from content.
    
    Args:
        content: Full note content
        
    Returns:
        Tuple of (frontmatter, main_content, original_separator)
        If no frontmatter, returns ("", content, "")
    """
    if not content.startswith('---'):
        return "", content, ""
    
    # Find the closing --- (must be at start of line)
    lines = content.split('\n')
    closing_index = None
    
    for i, line in enumerate(lines[1:], 1):  # Start from line 1
        if line.strip() == '---':
            closing_index = i
            break
    
    if closing_index is None:
        # No closing ---, treat as regular content
        return "", content, ""
    
    # Extract frontmatter (including delimiters)
    frontmatter_lines = lines[:closing_index + 1]
    frontmatter = '\n'.join(frontmatter_lines)
    
    # Extract main content (everything after frontmatter)
    main_content_lines = lines[closing_index + 1:]
    main_content = '\n'.join(main_content_lines)
    
    return frontmatter, main_content, '\n'


def _find_section_boundaries(content: str, section_identifier: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Find the start and end boundaries of a section in markdown content.
    
    Args:
        content: Markdown content to search
        section_identifier: Heading to find (e.g., "## Tasks", "### Status")
        
    Returns:
        Tuple of (start_line, end_line, actual_heading)
        Returns (None, None, None) if section not found
        
    Note:
        - start_line is the line index of the heading
        - end_line is the line index before the next heading of same/higher level (or EOF)
        - Matching is case-insensitive
    """
    lines = content.split('\n')
    
    # Parse the target heading level and text
    section_match = re.match(r'^(#{1,6})\s+(.+?)\s*#*$', section_identifier.strip())
    if not section_match:
        return None, None, None
    
    target_level = len(section_match.group(1))
    target_text = section_match.group(2).strip().lower()
    
    section_start = None
    actual_heading = None
    
    # Find the target section
    for i, line in enumerate(lines):
        heading_match = re.match(r'^(#{1,6})\s+(.+?)\s*#*$', line.strip())
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip().lower()
            
            if level == target_level and text == target_text:
                section_start = i
                actual_heading = line.strip()
                break
    
    if section_start is None:
        return None, None, None
    
    # Find the end of this section (next heading of same or higher level)
    section_end = len(lines)  # Default to end of file
    
    for i in range(section_start + 1, len(lines)):
        heading_match = re.match(r'^(#{1,6})\s+', lines[i].strip())
        if heading_match:
            level = len(heading_match.group(1))
            if level <= target_level:  # Same or higher level heading
                section_end = i
                break
    
    return section_start, section_end, actual_heading


def _create_section_content(heading: str, content: str, target_level: int) -> str:
    """
    Create a new section with proper heading formatting.
    
    Args:
        heading: Section heading text (without # markers)
        content: Content to add under the heading
        target_level: Heading level (1-6)
        
    Returns:
        Formatted section content
    """
    heading_prefix = '#' * target_level
    section_content = f"{heading_prefix} {heading}\n"
    
    if content.strip():
        section_content += f"\n{content}"
    
    return section_content


async def edit_note_section(
    path: str,
    section_identifier: str,
    content: str,
    operation: Literal["insert_after", "insert_before", "replace_section", "append_to_section", "edit_heading"] = "insert_after",
    create_if_missing: bool = False,
    ctx: Optional[Context] = None
) -> dict:
    """
    Edit a specific section of a note identified by a markdown heading.
    
    This tool enables token-efficient editing by targeting specific sections
    instead of rewriting entire notes. It preserves frontmatter and handles
    various section editing operations.
    
    Args:
        path: Path to the note to edit
        section_identifier: Markdown heading that identifies the section (e.g., "## Tasks", "### Status")
        content: Content to insert, replace, or append
        operation: How to edit the section:
            - "insert_after": Add content immediately after the section heading
            - "insert_before": Add content immediately before the section heading  
            - "replace_section": Replace entire section including heading
            - "append_to_section": Add content at the end of the section (before next heading)
            - "edit_heading": Change just the heading text while preserving section content
        create_if_missing: Create the section if it doesn't exist (default: false)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing edit status and details
        
    Examples:
        # Add tasks to a specific section
        >>> await edit_note_section(
        ...     "Daily/2024-01-15.md",
        ...     "## Tasks", 
        ...     "- [ ] Review PR\\n- [ ] Update docs",
        ...     operation="append_to_section"
        ... )
        
        # Update a status section
        >>> await edit_note_section(
        ...     "Projects/Website.md",
        ...     "### Current Status",
        ...     "### Current Status\\n\\nPhase 2 completed!",
        ...     operation="replace_section"
        ... )
        
        # Change just a heading
        >>> await edit_note_section(
        ...     "Projects/Website.md", 
        ...     "## Old Heading",
        ...     "## New Heading",
        ...     operation="edit_heading"
        ... )
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    # Validate content for non-heading operations
    if operation != "edit_heading":
        is_valid, error_msg = validate_content(content)
        if not is_valid:
            raise ValueError(error_msg)
    
    # Sanitize path
    path = sanitize_path(path)
    
    if ctx:
        ctx.info(f"Editing section '{section_identifier}' in note: {path}")
    
    vault = get_vault()
    
    # Read the existing note
    try:
        existing_note = await vault.read_note(path)
        note_content = existing_note.content
    except FileNotFoundError:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Separate frontmatter from content
    frontmatter, main_content, separator = _detect_frontmatter(note_content)
    
    # Find section boundaries
    start_line, end_line, actual_heading = _find_section_boundaries(main_content, section_identifier)
    
    if start_line is None:
        if not create_if_missing:
            raise ValueError(f"Section '{section_identifier}' not found in note. Use create_if_missing=true to create it.")
        
        # Create new section at end of document
        lines = main_content.split('\n')
        
        # Parse section identifier to get level and text
        section_match = re.match(r'^(#{1,6})\s+(.+?)\s*#*$', section_identifier.strip())
        if not section_match:
            raise ValueError(f"Invalid section identifier format: {section_identifier}")
        
        target_level = len(section_match.group(1))
        heading_text = section_match.group(2).strip()
        
        # Add new section
        if operation == "edit_heading":
            # For edit_heading, use the content as the new heading
            new_section = content.strip()
        elif operation == "replace_section":
            new_section = content
        else:
            new_section = _create_section_content(heading_text, content, target_level)
        
        # Ensure proper spacing
        if lines and lines[-1].strip():
            lines.append("")  # Add blank line before new section
        lines.append(new_section)
        
        modified_content = '\n'.join(lines)
        section_created = True
        operation_performed = "created"
    else:
        # Edit existing section
        lines = main_content.split('\n')
        section_created = False
        
        if operation == "insert_after":
            # Insert content immediately after the heading
            lines.insert(start_line + 1, content)
            operation_performed = "inserted_after"
            
        elif operation == "insert_before":
            # Insert content immediately before the heading
            lines.insert(start_line, content)
            operation_performed = "inserted_before"
            
        elif operation == "replace_section":
            # Replace entire section including heading
            del lines[start_line:end_line]
            lines.insert(start_line, content)
            operation_performed = "replaced"
            
        elif operation == "append_to_section":
            # Add content at the end of the section (before next heading or EOF)
            insert_position = end_line
            # If there's content in the section, add a blank line before new content
            if end_line > start_line + 1:
                lines.insert(insert_position, "")
                insert_position += 1
            lines.insert(insert_position, content)
            operation_performed = "appended"
            
        elif operation == "edit_heading":
            # Change just the heading text
            lines[start_line] = content.strip()
            operation_performed = "heading_edited"
        
        modified_content = '\n'.join(lines)
    
    # Reconstruct full content with frontmatter
    if frontmatter:
        final_content = frontmatter + separator + modified_content
    else:
        final_content = modified_content
    
    # Write the updated note
    note = await vault.write_note(path, final_content, overwrite=True)
    
    # Return standardized success structure
    return {
        "success": True,
        "path": note.path,
        "operation": "section_edited",
        "details": {
            "section_identifier": section_identifier,
            "edit_operation": operation_performed,
            "section_created": section_created,
            "section_found": start_line is not None,
            "frontmatter_preserved": bool(frontmatter),
            "metadata": note.metadata.model_dump(exclude_none=True)
        }
    }


async def edit_note_content(
    path: str,
    search_text: str,
    replacement_text: str,
    occurrence: Literal["first", "all"] = "first",
    ctx: Optional[Context] = None
) -> dict:
    """
    Edit specific text content in a note using precise search and replace.
    
    This tool enables token-efficient editing by replacing specific text
    without rewriting entire notes. It's ideal for updating values, fixing
    typos, or making targeted changes to any part of the note.
    
    Use this tool when you need to:
    - Update specific values or references
    - Fix typos or correct text
    - Modify frontmatter properties
    - Change URLs or links
    - Update dates or numbers
    
    Args:
        path: Path to the note to edit
        search_text: Exact text to search for and replace
        replacement_text: Text to replace the search_text with
        occurrence: Replace "first" occurrence only or "all" occurrences
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing edit status and replacement details
        
    Examples:
        # Update a specific value
        >>> await edit_note_content(
        ...     "Projects/Website.md",
        ...     "Status: In Progress",
        ...     "Status: Completed"
        ... )
        
        # Fix a typo throughout the document
        >>> await edit_note_content(
        ...     "Notes/Research.md",
        ...     "recieve",
        ...     "receive",
        ...     occurrence="all"
        ... )
        
        # Update frontmatter property
        >>> await edit_note_content(
        ...     "Daily/2024-01-15.md",
        ...     "priority: low",
        ...     "priority: high"
        ... )
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    # Validate inputs
    if not search_text:
        raise ValueError("search_text cannot be empty")
    
    if not isinstance(replacement_text, str):
        raise ValueError("replacement_text must be a string")
    
    # Sanitize path
    path = sanitize_path(path)
    
    if ctx:
        ctx.info(f"Searching and replacing text in note: {path}")
    
    vault = get_vault()
    
    # Read the existing note
    try:
        existing_note = await vault.read_note(path)
        original_content = existing_note.content
    except FileNotFoundError:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Perform replacement
    if occurrence == "first":
        if search_text not in original_content:
            raise ValueError(f"Search text not found: '{search_text}'")
        
        modified_content = original_content.replace(search_text, replacement_text, 1)
        replacements_made = 1
        
    elif occurrence == "all":
        count_before = original_content.count(search_text)
        if count_before == 0:
            raise ValueError(f"Search text not found: '{search_text}'")
        
        modified_content = original_content.replace(search_text, replacement_text)
        replacements_made = count_before
        
    else:
        raise ValueError(f"Invalid occurrence value: {occurrence}. Must be 'first' or 'all'")
    
    # Check if any changes were actually made
    if modified_content == original_content:
        return {
            "success": True,
            "path": path,
            "operation": "no_changes",
            "details": {
                "search_text": search_text,
                "replacement_text": replacement_text,
                "replacements_made": 0,
                "occurrence": occurrence,
                "reason": "Search text and replacement text are identical"
            }
        }
    
    # Write the updated note
    note = await vault.write_note(path, modified_content, overwrite=True)
    
    # Return standardized success structure
    return {
        "success": True,
        "path": note.path,
        "operation": "content_edited",
        "details": {
            "search_text": search_text,
            "replacement_text": replacement_text,
            "replacements_made": replacements_made,
            "occurrence": occurrence,
            "content_length_before": len(original_content),
            "content_length_after": len(modified_content),
            "metadata": note.metadata.model_dump(exclude_none=True)
        }
    }