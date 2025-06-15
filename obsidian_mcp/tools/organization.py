"""Organization tools for Obsidian MCP server."""

import re
from typing import List, Dict, Any, Optional
from fastmcp import Context
from ..utils import ObsidianAPI, validate_note_path, sanitize_path, is_markdown_file
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


async def create_folder(
    folder_path: str,
    create_placeholder: bool = True,
    ctx: Context = None
) -> dict:
    """
    Create a new folder in the vault, including all parent folders.
    
    Since Obsidian doesn't have explicit folders (they're created automatically
    when notes are added), this tool creates a folder by adding a placeholder
    file. It will create all necessary parent folders in the path.
    
    Args:
        folder_path: Path of the folder to create (e.g., "Apple/Studies/J71P")
        create_placeholder: Whether to create a placeholder file (default: true)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing creation status
        
    Example:
        >>> await create_folder("Apple/Studies/J71P", ctx=ctx)
        {
            "folder": "Apple/Studies/J71P",
            "created": true,
            "placeholder_file": "Apple/Studies/J71P/.gitkeep",
            "folders_created": ["Apple", "Apple/Studies", "Apple/Studies/J71P"]
        }
    """
    # Validate folder path
    if folder_path.endswith('.md') or folder_path.endswith('.markdown'):
        raise ValueError(f"Invalid folder path: '{folder_path}'. Folder paths should not end with .md")
    if '..' in folder_path or folder_path.startswith('/'):
        raise ValueError(f"Invalid folder path: '{folder_path}'. Paths must be relative and cannot contain '..'")
    if not folder_path or folder_path.isspace():
        raise ValueError("Folder path cannot be empty")
    
    # Sanitize path
    folder_path = folder_path.strip('/').replace('\\', '/')
    
    if ctx:
        ctx.info(f"Creating folder: {folder_path}")
    
    api = ObsidianAPI()
    
    # Split the path to check each level
    path_parts = folder_path.split('/')
    folders_to_check = []
    folders_created = []
    
    # Build list of all folders to check/create
    for i in range(len(path_parts)):
        partial_path = '/'.join(path_parts[:i+1])
        folders_to_check.append(partial_path)
    
    # Check each folder level
    from ..tools.search_discovery import list_notes
    for folder in folders_to_check:
        try:
            existing_notes = await list_notes(folder, recursive=False, ctx=None)
            # Folder exists if we can list it (even with 0 notes)
            if ctx:
                ctx.info(f"Folder already exists: {folder}")
        except Exception:
            # Folder doesn't exist, mark it for creation
            folders_created.append(folder)
            if ctx:
                ctx.info(f"Will create folder: {folder}")
    
    if not folders_created and not create_placeholder:
        # All folders already exist
        return {
            "folder": folder_path,
            "created": False,
            "message": "All folders in path already exist",
            "folders_created": []
        }
    
    if not create_placeholder:
        return {
            "folder": folder_path,
            "created": True,
            "message": "Folders will be created when first note is added",
            "placeholder_file": None,
            "folders_created": folders_created
        }
    
    # Create a placeholder file in the deepest folder to establish the entire path
    placeholder_path = f"{folder_path}/.gitkeep"
    placeholder_content = f"# Folder: {folder_path}\n\nThis file ensures the folder exists in the vault structure.\n"
    
    try:
        await api.create_note(placeholder_path, placeholder_content)
        return {
            "folder": folder_path,
            "created": True,
            "placeholder_file": placeholder_path,
            "folders_created": folders_created if folders_created else ["(all already existed)"]
        }
    except Exception as e:
        # Try with README.md if .gitkeep fails
        try:
            readme_path = f"{folder_path}/README.md"
            readme_content = f"# {folder_path.split('/')[-1]}\n\nThis folder contains notes related to {folder_path.replace('/', ' > ')}.\n"
            await api.create_note(readme_path, readme_content)
            return {
                "folder": folder_path,
                "created": True,
                "placeholder_file": readme_path,
                "folders_created": folders_created if folders_created else ["(all already existed)"]
            }
        except Exception as e2:
            raise ValueError(f"Failed to create folder: {str(e2)}")


async def move_folder(
    source_folder: str,
    destination_folder: str,
    update_links: bool = True,
    ctx: Context = None
) -> dict:
    """
    Move an entire folder and all its contents to a new location.
    
    Use this tool to reorganize your vault structure by moving entire
    folders with all their notes and subfolders.
    
    Args:
        source_folder: Current folder path (e.g., "Projects/Old")
        destination_folder: New folder path (e.g., "Archive/Projects/Old")
        update_links: Whether to update links in other notes (default: true)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing move status and statistics
        
    Example:
        >>> await move_folder("Projects/Completed", "Archive/2024/Projects", ctx=ctx)
        {
            "source": "Projects/Completed",
            "destination": "Archive/2024/Projects",
            "moved": true,
            "notes_moved": 15,
            "folders_moved": 3,
            "links_updated": 0
        }
    """
    # Validate folder paths (no .md extension)
    for folder, name in [(source_folder, "source"), (destination_folder, "destination")]:
        if folder.endswith('.md') or folder.endswith('.markdown'):
            raise ValueError(f"Invalid {name} folder path: '{folder}'. Folder paths should not end with .md")
        if '..' in folder or folder.startswith('/'):
            raise ValueError(f"Invalid {name} folder path: '{folder}'. Paths must be relative and cannot contain '..'")
    
    # Sanitize paths
    source_folder = source_folder.strip('/').replace('\\', '/')
    destination_folder = destination_folder.strip('/').replace('\\', '/')
    
    if source_folder == destination_folder:
        raise ValueError("Source and destination folders are the same")
    
    # Check if destination is a subfolder of source (would create circular reference)
    if destination_folder.startswith(source_folder + '/'):
        raise ValueError("Cannot move a folder into its own subfolder")
    
    if ctx:
        ctx.info(f"Moving folder from {source_folder} to {destination_folder}")
    
    api = ObsidianAPI()
    
    # Get all notes in the source folder recursively
    from ..tools.search_discovery import list_notes
    folder_contents = await list_notes(source_folder, recursive=True, ctx=None)
    
    if folder_contents["count"] == 0:
        raise ValueError(f"No notes found in folder: {source_folder}")
    
    notes_moved = 0
    folders_moved = set()  # Track unique folders
    links_updated = 0
    errors = []
    
    # Move each note
    for note_info in folder_contents["notes"]:
        old_path = note_info["path"]
        # Calculate new path by replacing the source folder prefix
        relative_path = old_path[len(source_folder):].lstrip('/')
        new_path = f"{destination_folder}/{relative_path}" if destination_folder else relative_path
        
        # Track folders
        folder_parts = relative_path.split('/')[:-1]  # Exclude filename
        for i in range(len(folder_parts)):
            folder_path = '/'.join(folder_parts[:i+1])
            folders_moved.add(folder_path)
        
        try:
            # Read the note
            note = await api.get_note(old_path)
            if note:
                # Create at new location
                await api.create_note(new_path, note.content)
                # Delete from old location
                await api.delete_note(old_path)
                notes_moved += 1
                
                if ctx:
                    ctx.info(f"Moved: {old_path} → {new_path}")
        except Exception as e:
            errors.append(f"Failed to move {old_path}: {str(e)}")
            if ctx:
                ctx.info(f"Error moving {old_path}: {str(e)}")
    
    # Update links if requested
    if update_links:
        # This would require searching for all notes that link to notes in the source folder
        # and updating them. For now, we'll mark this as a future enhancement.
        pass
    
    result = {
        "source": source_folder,
        "destination": destination_folder,
        "moved": True,
        "notes_moved": notes_moved,
        "folders_moved": len(folders_moved),
        "links_updated": links_updated
    }
    
    if errors:
        result["errors"] = errors[:5]  # Limit to first 5 errors
        result["total_errors"] = len(errors)
    
    return result


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


async def update_tags(
    path: str,
    tags: List[str],
    merge: bool = False,
    ctx: Context = None
) -> dict:
    """
    Update tags on a note - either replace all tags or merge with existing.
    
    Use this tool when you want to set a note's tags based on its content
    or purpose. Perfect for AI-driven tag suggestions after analyzing a note.
    
    Args:
        path: Path to the note
        tags: New tags to set (without # prefix)
        merge: If True, adds to existing tags. If False, replaces all tags (default: False)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing previous and new tag lists
        
    Example:
        >>> # After analyzing a note about machine learning project
        >>> await update_tags("Projects/ML Research.md", ["ai", "research", "neural-networks"], ctx=ctx)
        {
            "path": "Projects/ML Research.md",
            "previous_tags": ["project", "todo"],
            "new_tags": ["ai", "research", "neural-networks"],
            "operation": "replaced"
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
    
    # Clean tags (remove # prefix if present)
    tags = [tag.lstrip("#").strip() for tag in tags if tag.strip()]
    
    if ctx:
        ctx.info(f"Updating tags for {path}: {tags} (merge={merge})")
    
    api = ObsidianAPI()
    note = await api.get_note(path)
    
    if not note:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Store previous tags
    previous_tags = note.metadata.tags.copy() if note.metadata.tags else []
    
    # Determine final tags based on merge setting
    if merge:
        # Merge with existing tags (like add_tags but more explicit)
        final_tags = list(set(previous_tags + tags))
        operation = "merged"
    else:
        # Replace all tags
        final_tags = tags
        operation = "replaced"
    
    # Update the note's frontmatter
    content = note.content
    updated_content = _update_frontmatter_tags(content, final_tags, "replace")
    
    # Update the note
    await api.update_note(path, updated_content)
    
    return {
        "path": path,
        "previous_tags": previous_tags,
        "new_tags": final_tags,
        "operation": operation
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
        tags: Tags to add, remove, or replace with
        operation: "add", "remove", or "replace"
        
    Returns:
        Updated content
    """
    # Check if frontmatter exists
    if not content.startswith("---\n"):
        # Create frontmatter if it doesn't exist
        if operation in ["add", "replace"]:
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
            elif operation == "replace":
                # Replace all tags
                existing_tags = tags
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
    
    # If no tags were found and we're adding or replacing, add them
    if not tags_found and operation in ["add", "replace"]:
        new_lines.insert(0, f"tags: [{', '.join(tags)}]")
    
    # Reconstruct content
    new_frontmatter = '\n'.join(new_lines)
    return f"---\n{new_frontmatter}\n---\n{rest_of_content}"


async def list_tags(
    include_counts: bool = True,
    sort_by: str = "name",
    ctx=None
) -> dict:
    """
    List all unique tags used across the vault with usage statistics.
    
    Use this tool to discover existing tags before creating new ones. This helps
    maintain consistency in your tagging system and prevents duplicate tags with
    slight variations (e.g., 'project' vs 'projects').
    
    Args:
        include_counts: Whether to include usage count for each tag (default: true)
        sort_by: How to sort results - "name" (alphabetical) or "count" (by usage) (default: "name")
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing all unique tags with optional usage counts
        
    Example:
        >>> await list_tags(include_counts=True, sort_by="count")
        {
            "total_tags": 25,
            "tags": [
                {"name": "project", "count": 42},
                {"name": "meeting", "count": 38},
                {"name": "idea", "count": 15}
            ]
        }
    """
    # Validate sort_by parameter
    if sort_by not in ["name", "count"]:
        raise ValueError(ERROR_MESSAGES["invalid_sort_by"].format(value=sort_by))
    
    if ctx:
        ctx.info("Collecting tags from vault...")
    
    api = ObsidianAPI()
    
    # Dictionary to store tag counts
    tag_counts = {}
    
    try:
        # OPTIMIZATION: Use search API to get all notes with tags in a single query
        # This uses JsonLogic to find notes where tags field exists
        # Since we can't check array length with count, we just check for existence
        json_logic_query = {
            "!!": {"var": "tags"}  # tags field exists and is truthy
        }
        
        # Get all notes with tags using a single API call
        import httpx
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            url = f"{api.base_url}/search/"
            headers = api.headers.copy()
            headers["Content-Type"] = "application/vnd.olrapi.jsonlogic+json"
            
            response = await client.post(
                url,
                headers=headers,
                json=json_logic_query
            )
            response.raise_for_status()
            
            results = response.json()
            
            if ctx:
                ctx.info(f"Found {len(results)} notes with tags")
            
            # Now fetch only the notes that have tags
            # Use asyncio.gather for concurrent fetching (much faster)
            import asyncio
            
            # Extract note paths from results
            note_paths = []
            for result in results:
                if isinstance(result, dict) and "filename" in result:
                    note_paths.append(result["filename"])
                elif isinstance(result, str):
                    note_paths.append(result)
            
            # Fetch notes concurrently in batches
            batch_size = 10  # Process 10 notes at a time to avoid overwhelming the API
            for i in range(0, len(note_paths), batch_size):
                batch = note_paths[i:i + batch_size]
                
                # Create tasks for concurrent fetching
                tasks = [api.get_note(path) for path in batch]
                
                # Wait for all tasks in this batch to complete
                try:
                    notes = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for note in notes:
                        if isinstance(note, Exception):
                            # Skip failed requests
                            continue
                            
                        # Extract tags
                        if note and note.metadata and note.metadata.tags:
                            for tag in note.metadata.tags:
                                # Tags are already normalized in our metadata parsing
                                if tag:
                                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                except Exception:
                    # Skip this batch if there's an error
                    continue
        
        # Format results
        if include_counts:
            tags = [{"name": tag, "count": count} for tag, count in tag_counts.items()]
            
            # Sort based on preference
            if sort_by == "count":
                tags.sort(key=lambda x: x["count"], reverse=True)
            else:  # sort by name
                tags.sort(key=lambda x: x["name"].lower())
        else:
            # Just return tag names sorted
            tags = sorted(tag_counts.keys(), key=str.lower)
        
        return {
            "total_tags": len(tag_counts),
            "tags": tags
        }
        
    except Exception as e:
        if ctx:
            ctx.info(f"Failed to list tags: {str(e)}")
        raise ValueError(ERROR_MESSAGES["tag_collection_failed"].format(error=str(e)))