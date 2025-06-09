"""Link management tools for Obsidian MCP server."""

import re
from typing import List, Optional, Dict, Set
from ..utils import ObsidianAPI, is_markdown_file
from ..utils.validation import validate_note_path
from ..models import Backlink
from ..constants import ERROR_MESSAGES


# Regular expressions for matching different link formats in Obsidian
WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]')
MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def extract_links_from_content(content: str) -> List[Dict[str, str]]:
    """
    Extract all links from note content.
    
    Supports both wiki-style links [[Note]] and markdown links [text](note.md).
    
    Args:
        content: The markdown content to parse
        
    Returns:
        List of dictionaries with link information
    """
    links = []
    
    # Extract wiki-style links [[Note]] or [[Note|Alias]] or [[Note#Header]]
    for match in WIKI_LINK_PATTERN.finditer(content):
        note_path = match.group(1).strip()
        header = match.group(2)
        alias = match.group(3)
        
        # Get the display text - use alias if provided, otherwise the note name
        display_text = alias.strip() if alias else note_path
        
        # Normalize the path - add .md extension if not present
        if not note_path.endswith('.md'):
            note_path += '.md'
            
        link_info = {
            'path': note_path,
            'display_text': display_text,
            'type': 'wiki'
        }
        
        if header:
            link_info['header'] = header.strip()
            
        links.append(link_info)
    
    # Extract markdown-style links [text](path.md)
    for match in MARKDOWN_LINK_PATTERN.finditer(content):
        display_text = match.group(1).strip()
        link_path = match.group(2).strip()
        
        # Only consider internal links (not URLs)
        if not link_path.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
            # Handle relative paths and fragments
            if link_path.startswith('#'):
                # This is a link to a header in the same file
                continue
                
            links.append({
                'path': link_path,
                'display_text': display_text,
                'type': 'markdown'
            })
    
    return links


def get_link_context(content: str, link_match: re.Match, context_length: int = 100) -> str:
    """
    Extract context around a link.
    
    Args:
        content: The full note content
        link_match: The regex match object for the link
        context_length: Number of characters to include before and after
        
    Returns:
        Context string with the link in the middle
    """
    start = max(0, link_match.start() - context_length // 2)
    end = min(len(content), link_match.end() + context_length // 2)
    
    context = content[start:end].strip()
    
    # Add ellipsis if truncated
    if start > 0:
        context = "..." + context
    if end < len(content):
        context = context + "..."
        
    return context


async def get_backlinks(
    path: str,
    include_context: bool = True,
    context_length: int = 100,
    ctx=None
) -> dict:
    """
    Find all notes that link to a specific note.
    
    This tool discovers which notes reference the target note, helping you understand
    how information is connected in your vault. Backlinks are essential for
    understanding the relationships between your notes.
    
    Args:
        path: Path to the note to find backlinks for
        include_context: Whether to include text context around links (default: true)
        context_length: Number of characters of context to include (default: 100)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing all notes that link to the target note
        
    Example:
        >>> await get_backlinks("Projects/AI Research.md", ctx=ctx)
        {
            "target_note": "Projects/AI Research.md",
            "backlink_count": 5,
            "backlinks": [
                {
                    "source_path": "Daily/2024-01-15.md",
                    "link_text": "AI Research",
                    "context": "...working on the [[AI Research]] project today..."
                }
            ]
        }
    """
    # Validate the note path
    is_valid, error = validate_note_path(path)
    if not is_valid:
        raise ValueError(error)
    
    if ctx:
        ctx.info(f"Finding backlinks to: {path}")
    
    api = ObsidianAPI()
    
    # Verify the target note exists
    try:
        note = await api.get_note(path)
        if not note:
            raise FileNotFoundError(f"Note not found: {path}")
    except Exception:
        raise FileNotFoundError(f"Note not found: {path}")
    
    # Get all notes in the vault
    all_notes = []
    
    async def collect_notes_from_directory(directory: str = ""):
        """Recursively collect all note paths from a directory."""
        try:
            items = await api.get_vault_structure(directory)
            for item in items:
                # Construct full path
                full_path = f"{directory}/{item.path}" if directory else item.path
                
                if item.is_folder:
                    # Recursively collect from subdirectory
                    await collect_notes_from_directory(full_path)
                elif is_markdown_file(full_path):
                    all_notes.append(full_path)
        except Exception:
            # Skip directories we can't access
            pass
    
    # Start collecting from root
    await collect_notes_from_directory()
    
    # Search each note for links to the target
    backlinks = []
    
    # Create variations of the target path to match against
    target_names = [path]
    
    # Also check without .md extension
    if path.endswith('.md'):
        target_names.append(path[:-3])
    
    # Also check just the filename without folder path
    # This handles cases where notes link to "Apple TOC" instead of "Images/Apple TOC"
    filename = path.split('/')[-1]
    if filename not in target_names:
        target_names.append(filename)
    
    if filename.endswith('.md'):
        filename_no_ext = filename[:-3]
        if filename_no_ext not in target_names:
            target_names.append(filename_no_ext)
    
    if ctx:
        ctx.info(f"Will match against variations: {target_names}")
    
    for note_path in all_notes:
        if note_path == path:
            # Skip the target note itself
            continue
            
        try:
            # Read the note content
            note = await api.get_note(note_path)
            if not note:
                continue
            content = note.content
            
            # Check for wiki-style links to the target
            for match in WIKI_LINK_PATTERN.finditer(content):
                linked_path = match.group(1).strip()
                
                # Normalize the linked path
                if not linked_path.endswith('.md'):
                    linked_path += '.md'
                
                if linked_path in target_names:
                    alias = match.group(3)
                    link_text = alias.strip() if alias else match.group(1).strip()
                    
                    backlink_info = {
                        'source_path': note_path,
                        'link_text': link_text,
                        'link_type': 'wiki'
                    }
                    
                    if include_context:
                        backlink_info['context'] = get_link_context(content, match, context_length)
                    
                    backlinks.append(backlink_info)
                    
                    if ctx:
                        ctx.info(f"Found backlink in {note_path}: {link_text}")
            
            # Check for markdown-style links to the target
            for match in MARKDOWN_LINK_PATTERN.finditer(content):
                link_path = match.group(2).strip()
                
                if link_path in target_names:
                    backlink_info = {
                        'source_path': note_path,
                        'link_text': match.group(1).strip(),
                        'link_type': 'markdown'
                    }
                    
                    if include_context:
                        backlink_info['context'] = get_link_context(content, match, context_length)
                    
                    backlinks.append(backlink_info)
                    
        except Exception:
            # Skip notes that can't be read
            continue
    
    if ctx:
        ctx.info(f"Found {len(backlinks)} backlinks")
    
    return {
        'target_note': path,
        'backlink_count': len(backlinks),
        'backlinks': backlinks
    }


async def get_outgoing_links(
    path: str,
    check_validity: bool = False,
    ctx=None
) -> dict:
    """
    List all links from a specific note.
    
    This tool extracts all outgoing links from a note, helping you understand
    what other notes and resources this note references. Useful for navigation
    and understanding note dependencies.
    
    Args:
        path: Path to the note to extract links from
        check_validity: Whether to check if linked notes exist (default: false)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing all outgoing links from the note
        
    Example:
        >>> await get_outgoing_links("Projects/Overview.md", check_validity=True, ctx=ctx)
        {
            "source_note": "Projects/Overview.md",
            "link_count": 8,
            "links": [
                {
                    "path": "Projects/AI Research.md",
                    "display_text": "AI Research",
                    "type": "wiki",
                    "exists": true
                }
            ]
        }
    """
    # Validate the note path
    is_valid, error = validate_note_path(path)
    if not is_valid:
        raise ValueError(error)
    
    if ctx:
        ctx.info(f"Extracting links from: {path}")
    
    api = ObsidianAPI()
    
    # Read the note content
    try:
        note = await api.get_note(path)
        if not note:
            raise FileNotFoundError(f"Note not found: {path}")
    except Exception:
        raise FileNotFoundError(f"Note not found: {path}")
    
    content = note.content
    
    # Extract all links
    links = extract_links_from_content(content)
    
    # Check validity if requested
    if check_validity:
        for link in links:
            try:
                note = await api.get_note(link['path'])
                link['exists'] = note is not None
            except Exception:
                link['exists'] = False
    
    if ctx:
        ctx.info(f"Found {len(links)} outgoing links")
    
    return {
        'source_note': path,
        'link_count': len(links),
        'links': links
    }


async def find_broken_links(
    directory: Optional[str] = None,
    ctx=None
) -> dict:
    """
    Find all broken links in the vault or a specific directory.
    
    This tool identifies links pointing to non-existent notes, helping maintain
    vault integrity. Broken links often occur after renaming or deleting notes.
    Regular checks help keep your knowledge base well-connected.
    
    Args:
        directory: Specific directory to check (optional, defaults to entire vault)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing all broken links found
        
    Example:
        >>> await find_broken_links("Projects", ctx=ctx)
        {
            "directory": "Projects",
            "broken_link_count": 3,
            "affected_notes": 2,
            "broken_links": [
                {
                    "source_path": "Projects/Overview.md",
                    "broken_link": "Projects/Old Name.md",
                    "link_text": "Old Project",
                    "link_type": "wiki"
                }
            ]
        }
    """
    if ctx:
        scope = f"directory: {directory}" if directory else "entire vault"
        ctx.info(f"Checking for broken links in {scope}")
    
    api = ObsidianAPI()
    
    # Get all notes to check
    notes_to_check = []
    
    async def collect_notes_from_directory(dir_path: str = ""):
        """Recursively collect all note paths from a directory."""
        try:
            items = await api.get_vault_structure(dir_path)
            for item in items:
                # Construct full path
                full_path = f"{dir_path}/{item.path}" if dir_path else item.path
                
                if item.is_folder:
                    # Recursively collect from subdirectory
                    await collect_notes_from_directory(full_path)
                elif is_markdown_file(full_path):
                    notes_to_check.append(full_path)
        except Exception:
            # Skip directories we can't access
            pass
    
    # Start collecting from the specified directory or root
    await collect_notes_from_directory(directory or "")
    
    # Track broken links and affected notes
    broken_links = []
    affected_notes_set = set()
    
    # Check each note for broken links
    for note_path in notes_to_check:
        try:
            # Read the note content
            note = await api.get_note(note_path)
            if not note:
                continue
            content = note.content
            
            # Extract all links
            links = extract_links_from_content(content)
            
            # Check each link
            for link in links:
                try:
                    linked_note = await api.get_note(link['path'])
                    if not linked_note:
                        # This is a broken link
                        broken_link_info = {
                            'source_path': note_path,
                            'broken_link': link['path'],
                            'link_text': link['display_text'],
                            'link_type': link['type']
                        }
                        
                        broken_links.append(broken_link_info)
                        affected_notes_set.add(note_path)
                except Exception:
                    # Consider any error as a broken link
                    broken_link_info = {
                        'source_path': note_path,
                        'broken_link': link['path'],
                        'link_text': link['display_text'],
                        'link_type': link['type']
                    }
                    
                    broken_links.append(broken_link_info)
                    affected_notes_set.add(note_path)
                    
        except Exception:
            # Skip notes that can't be read
            continue
    
    if ctx:
        ctx.info(f"Found {len(broken_links)} broken links in {len(affected_notes_set)} notes")
    
    # Sort broken links by source path for easier review
    broken_links.sort(key=lambda x: x['source_path'])
    
    return {
        'directory': directory or '/',
        'broken_link_count': len(broken_links),
        'affected_notes': len(affected_notes_set),
        'broken_links': broken_links
    }