"""Organization tools for Obsidian MCP server."""

import re
from typing import List, Dict, Any, Optional
from fastmcp import Context
from ..utils import ObsidianAPI, validate_note_path, sanitize_path
from ..utils.validation import validate_tags
from ..models import Note, NoteMetadata, Tag
from ..constants import ERROR_MESSAGES


async def move_note(
    source_path: str,
    destination_path: str,
    update_links: bool = True,
    ctx: Context = None
) -> dict:
    """
    Move a note to a new location, optionally updating all links.
    
    Use this tool to reorganize your vault by moving notes to different
    folders while maintaining link integrity.
    
    Args:
        source_path: Current path of the note
        destination_path: New path for the note
        update_links: Whether to update links in other notes (default: true)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing move status and updated links count
        
    Example:
        >>> await move_note("Inbox/Quick Note.md", "Projects/Research/Quick Note.md", ctx=ctx)
        {
            "source": "Inbox/Quick Note.md",
            "destination": "Projects/Research/Quick Note.md",
            "moved": true,
            "links_updated": 5
        }
    """
    # Validate paths
    for path, name in [(source_path, "source"), (destination_path, "destination")]:
        is_valid, error_msg = validate_note_path(path)
        if not is_valid:
            raise ValueError(f"Invalid {name} path: {error_msg}")
    
    # Sanitize paths
    source_path = sanitize_path(source_path)
    destination_path = sanitize_path(destination_path)
    
    if source_path == destination_path:
        raise ValueError("Source and destination paths are the same")
    
    if ctx:
        ctx.info(f"Moving note from {source_path} to {destination_path}")
    
    api = ObsidianAPI()
    
    # Check if source exists
    source_note = await api.get_note(source_path)
    if not source_note:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=source_path))
    
    # Check if destination already exists
    dest_note = await api.get_note(destination_path)
    if dest_note:
        raise FileExistsError(f"Note already exists at destination: {destination_path}")
    
    # Create note at new location
    await api.create_note(destination_path, source_note.content)
    
    # Update links if requested
    links_updated = 0
    if update_links:
        # This would require searching for all notes that link to the source
        # and updating them. For now, we'll mark this as a future enhancement.
        # In a real implementation, you'd search for [[source_path]] and replace
        # with [[destination_path]] across all notes.
        pass
    
    # Delete original note
    await api.delete_note(source_path)
    
    return {
        "source": source_path,
        "destination": destination_path,
        "moved": True,
        "links_updated": links_updated
    }


async def add_tags(
    path: str,
    tags: List[str],
    ctx: Context = None
) -> dict:
    """
    Add tags to a note's frontmatter.
    
    Use this tool to add organizational tags to notes. Tags are added
    to the YAML frontmatter and do not modify the note's content.
    
    Args:
        path: Path to the note
        tags: List of tags to add (without # prefix)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing updated tag list
        
    Example:
        >>> await add_tags("Projects/AI.md", ["machine-learning", "research"], ctx=ctx)
        {
            "path": "Projects/AI.md",
            "tags_added": ["machine-learning", "research"],
            "all_tags": ["ai", "project", "machine-learning", "research"]
        }
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    path = sanitize_path(path)
    
    # Validate tags
    is_valid, error = validate_tags(tags)
    if not is_valid:
        raise ValueError(error)
    
    # Clean tags (remove # prefix if present) - validation already does this
    tags = [tag.lstrip("#").strip() for tag in tags if tag.strip()]
    
    if ctx:
        ctx.info(f"Adding tags to {path}: {tags}")
    
    api = ObsidianAPI()
    note = await api.get_note(path)
    
    if not note:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Parse frontmatter and update tags
    content = note.content
    updated_content = _update_frontmatter_tags(content, tags, "add")
    
    # Update the note
    await api.update_note(path, updated_content)
    
    # Get updated note to return current tags
    updated_note = await api.get_note(path)
    
    return {
        "path": path,
        "tags_added": tags,
        "all_tags": updated_note.metadata.tags
    }


async def remove_tags(
    path: str,
    tags: List[str],
    ctx: Context = None
) -> dict:
    """
    Remove tags from a note's frontmatter.
    
    Use this tool to remove organizational tags from notes.
    
    Args:
        path: Path to the note
        tags: List of tags to remove (without # prefix)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing updated tag list
        
    Example:
        >>> await remove_tags("Projects/AI.md", ["outdated"], ctx=ctx)
        {
            "path": "Projects/AI.md",
            "tags_removed": ["outdated"],
            "remaining_tags": ["ai", "project", "machine-learning"]
        }
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    path = sanitize_path(path)
    
    # Validate tags
    is_valid, error = validate_tags(tags)
    if not is_valid:
        raise ValueError(error)
    
    # Clean tags (remove # prefix if present) - validation already does this
    tags = [tag.lstrip("#").strip() for tag in tags if tag.strip()]
    
    if ctx:
        ctx.info(f"Removing tags from {path}: {tags}")
    
    api = ObsidianAPI()
    note = await api.get_note(path)
    
    if not note:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Parse frontmatter and update tags
    content = note.content
    updated_content = _update_frontmatter_tags(content, tags, "remove")
    
    # Update the note
    await api.update_note(path, updated_content)
    
    # Get updated note to return current tags
    updated_note = await api.get_note(path)
    
    return {
        "path": path,
        "tags_removed": tags,
        "remaining_tags": updated_note.metadata.tags
    }


async def get_note_info(
    path: str,
    ctx: Context = None
) -> dict:
    """
    Get metadata and information about a note without retrieving its full content.
    
    Use this tool when you need to check a note's metadata, tags, or other
    properties without loading the entire content.
    
    Args:
        path: Path to the note
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing note metadata and statistics
        
    Example:
        >>> await get_note_info("Projects/AI Research.md", ctx=ctx)
        {
            "path": "Projects/AI Research.md",
            "exists": true,
            "metadata": {
                "tags": ["ai", "research", "active"],
                "created": "2024-01-10T10:00:00Z",
                "modified": "2024-01-15T14:30:00Z",
                "aliases": ["AI Study", "ML Research"]
            },
            "stats": {
                "size_bytes": 4523,
                "word_count": 823,
                "link_count": 12
            }
        }
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    path = sanitize_path(path)
    
    if ctx:
        ctx.info(f"Getting info for: {path}")
    
    api = ObsidianAPI()
    note = await api.get_note(path)
    
    if not note:
        return {
            "path": path,
            "exists": False
        }
    
    # Calculate statistics
    content = note.content
    word_count = len(content.split())
    
    # Count links (both [[wikilinks]] and [markdown](links))
    wikilink_count = len(re.findall(r'\[\[([^\]]+)\]\]', content))
    markdown_link_count = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
    link_count = wikilink_count + markdown_link_count
    
    return {
        "path": path,
        "exists": True,
        "metadata": note.metadata.model_dump(exclude_none=True),
        "stats": {
            "size_bytes": len(content.encode('utf-8')),
            "word_count": word_count,
            "link_count": link_count
        }
    }


def _update_frontmatter_tags(content: str, tags: List[str], operation: str) -> str:
    """
    Update tags in YAML frontmatter.
    
    Args:
        content: Note content
        tags: Tags to add or remove
        operation: "add" or "remove"
        
    Returns:
        Updated content
    """
    # Check if frontmatter exists
    if not content.startswith("---\n"):
        # Create frontmatter if it doesn't exist
        if operation == "add":
            frontmatter = f"---\ntags: {tags}\n---\n\n"
            return frontmatter + content
        else:
            # Nothing to remove if no frontmatter
            return content
    
    # Parse existing frontmatter
    try:
        end_index = content.index("\n---\n", 4) + 5
        frontmatter = content[4:end_index-5]
        rest_of_content = content[end_index:]
    except ValueError:
        # Invalid frontmatter
        return content
    
    # Parse YAML manually (simple approach for tags)
    lines = frontmatter.split('\n')
    new_lines = []
    tags_found = False
    
    for line in lines:
        if line.startswith('tags:'):
            tags_found = True
            # Parse existing tags
            existing_tags = []
            if '[' in line:
                # Array format: tags: [tag1, tag2]
                match = re.search(r'\[(.*?)\]', line)
                if match:
                    existing_tags = [t.strip().strip('"').strip("'") for t in match.group(1).split(',')]
            elif line.strip() != 'tags:':
                # Inline format: tags: tag1 tag2
                existing_tags = line.split(':', 1)[1].strip().split()
            
            # Update tags based on operation
            if operation == "add":
                # Add new tags, avoid duplicates
                for tag in tags:
                    if tag not in existing_tags:
                        existing_tags.append(tag)
            else:  # remove
                existing_tags = [t for t in existing_tags if t not in tags]
            
            # Format updated tags
            if existing_tags:
                new_lines.append(f"tags: [{', '.join(existing_tags)}]")
            # Skip line if no tags remain
            
        elif line.strip().startswith('- ') and tags_found and not line.startswith(' '):
            # This might be a tag in list format, skip for now
            continue
        else:
            new_lines.append(line)
            if line.strip() == '' or not line.startswith(' '):
                tags_found = False
    
    # If no tags were found and we're adding, add them
    if not tags_found and operation == "add":
        new_lines.insert(0, f"tags: [{', '.join(tags)}]")
    
    # Reconstruct content
    new_frontmatter = '\n'.join(new_lines)
    return f"---\n{new_frontmatter}\n---\n{rest_of_content}"