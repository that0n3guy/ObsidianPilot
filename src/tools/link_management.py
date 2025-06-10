"""Link management tools for Obsidian MCP server."""

import re
import asyncio
from typing import List, Optional, Dict, Set, Tuple
from ..utils import ObsidianAPI, is_markdown_file
from ..utils.validation import validate_note_path


# Regular expressions for matching different link types
WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]|]+)(\|([^\]]+))?\]\]')
MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

# Cache for vault structure to avoid repeated scans
_vault_notes_cache: Optional[Dict[str, str]] = None
_cache_timestamp: Optional[float] = None
CACHE_TTL = 300  # 5 minutes


async def build_vault_notes_index(api: ObsidianAPI, force_refresh: bool = False) -> Dict[str, str]:
    """
    Build an index of all notes in the vault.
    Maps note names to their full paths.
    
    This is cached for performance.
    """
    global _vault_notes_cache, _cache_timestamp
    import time
    
    # Check if we can use cache
    if not force_refresh and _vault_notes_cache is not None:
        if _cache_timestamp and (time.time() - _cache_timestamp) < CACHE_TTL:
            return _vault_notes_cache
    
    # Build fresh index
    notes_index = {}
    
    async def scan_directory(directory: str = ""):
        """Recursively scan directory and build index."""
        try:
            items = await api.get_vault_structure(directory)
            
            # Process all items in parallel
            tasks = []
            for item in items:
                full_path = f"{directory}/{item.path}" if directory else item.path
                
                if item.is_folder:
                    tasks.append(scan_directory(full_path))
                elif is_markdown_file(full_path):
                    # Map both with and without .md extension
                    note_name = item.name
                    notes_index[note_name] = full_path
                    if note_name.endswith('.md'):
                        notes_index[note_name[:-3]] = full_path
            
            # Wait for all subdirectory scans
            if tasks:
                await asyncio.gather(*tasks)
                
        except Exception:
            pass
    
    await scan_directory()
    
    # Update cache
    _vault_notes_cache = notes_index
    _cache_timestamp = time.time()
    
    return notes_index


async def find_notes_by_names(api: ObsidianAPI, note_names: List[str]) -> Dict[str, Optional[str]]:
    """
    Find multiple notes by their names efficiently.
    
    Returns a dict mapping requested names to their full paths (or None if not found).
    """
    # Build or get cached index
    notes_index = await build_vault_notes_index(api)
    
    results = {}
    for name in note_names:
        # Ensure .md extension for lookup
        lookup_name = name if name.endswith('.md') else name + '.md'
        
        # First check if it's already a full path that exists
        if lookup_name in notes_index.values():
            results[name] = lookup_name
        else:
            # Look up by filename
            results[name] = notes_index.get(lookup_name) or notes_index.get(name)
    
    return results


async def check_links_validity_batch(api: ObsidianAPI, links: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """
    Check validity of multiple links in batch for performance.
    """
    # Get unique paths to check
    unique_paths = list(set(link['path'] for link in links))
    
    # Find all notes in one go
    found_paths = await find_notes_by_names(api, unique_paths)
    
    # Update links with validity info
    results = []
    for link in links:
        link_copy = link.copy()
        found_path = found_paths.get(link['path'])
        link_copy['exists'] = found_path is not None
        if found_path and found_path != link['path']:
            link_copy['actual_path'] = found_path
        results.append(link_copy)
    
    return results


def extract_links_from_content(content: str) -> List[dict]:
    """
    Extract all links from note content.
    
    Finds both wiki-style ([[Link]]) and markdown-style ([text](link)) links.
    
    Args:
        content: The note content to extract links from
        
    Returns:
        List of link dictionaries with path, display text, and type
    """
    links = []
    
    # Extract wiki-style links
    for match in WIKI_LINK_PATTERN.finditer(content):
        link_path = match.group(1).strip()
        alias = match.group(3)
        
        # Ensure .md extension for internal links
        if not link_path.endswith('.md') and not link_path.startswith('http'):
            link_path += '.md'
        
        links.append({
            'path': link_path,
            'display_text': alias.strip() if alias else match.group(1).strip(),
            'type': 'wiki'
        })
    
    # Extract markdown-style links (only internal links, not URLs)
    for match in MARKDOWN_LINK_PATTERN.finditer(content):
        link_path = match.group(2).strip()
        
        # Skip external URLs
        if link_path.startswith('http://') or link_path.startswith('https://'):
            continue
        
        # Ensure .md extension
        if not link_path.endswith('.md'):
            link_path += '.md'
        
        links.append({
            'path': link_path,
            'display_text': match.group(1).strip(),
            'type': 'markdown'
        })
    
    return links


def get_link_context(content: str, match, context_length: int = 100) -> str:
    """
    Extract context around a link match.
    
    Args:
        content: The full content
        match: The regex match object
        context_length: Characters to include before and after
        
    Returns:
        Context string with the link highlighted
    """
    start = max(0, match.start() - context_length)
    end = min(len(content), match.end() + context_length)
    
    # Extract context
    context = content[start:end]
    
    # Add ellipsis if truncated
    if start > 0:
        context = "..." + context
    if end < len(content):
        context = context + "..."
    
    return context.strip()


async def get_backlinks(
    path: str,
    include_context: bool = True,
    context_length: int = 100,
    ctx=None
) -> dict:
    """
    Get all notes that link to the specified note (optimized version).
    
    This tool finds all backlinks (incoming links) to a specific note,
    helping understand how notes are connected and referenced.
    
    Args:
        path: Path to the target note
        include_context: Whether to include surrounding text context
        context_length: Characters of context to include (default 100)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing:
        - target_note: The note being linked to
        - backlink_count: Number of backlinks found
        - backlinks: List of backlink information including:
          - source_path: Note containing the link
          - link_text: The display text of the link
          - link_type: 'wiki' or 'markdown'
          - context: Surrounding text (if requested)
          
    Example:
        {
            "target_note": "Projects/My Project.md",
            "backlink_count": 3,
            "backlinks": [
                {
                    "source_path": "Daily/2024-01-15.md",
                    "link_text": "My Project",
                    "link_type": "wiki",
                    "context": "...working on [[My Project]] today..."
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
    note = await api.get_note(path)
    if not note:
        raise FileNotFoundError(f"Note not found: {path}")
    
    # Build notes index
    notes_index = await build_vault_notes_index(api)
    all_note_paths = list(set(notes_index.values()))  # Use set to get unique paths
    
    # Create variations of the target path to match against
    target_names = [path]
    if path.endswith('.md'):
        target_names.append(path[:-3])
    
    filename = path.split('/')[-1]
    if filename not in target_names:
        target_names.append(filename)
    if filename.endswith('.md'):
        filename_no_ext = filename[:-3]
        if filename_no_ext not in target_names:
            target_names.append(filename_no_ext)
    
    if ctx:
        ctx.info(f"Will match against variations: {target_names}")
        ctx.info(f"Scanning {len(all_note_paths)} notes...")
    
    # Process notes in parallel batches
    backlinks = []
    batch_size = 10  # Process 10 notes at a time
    
    async def check_note_for_backlinks(note_path: str) -> List[dict]:
        """Check a single note for backlinks."""
        if note_path == path:
            return []
        
        try:
            note = await api.get_note(note_path)
            if not note:
                return []
            
            content = note.content
            note_backlinks = []
            
            # Check for wiki-style links
            for match in WIKI_LINK_PATTERN.finditer(content):
                linked_path = match.group(1).strip()
                
                # Check if this link matches our target
                is_match = False
                if linked_path in target_names:
                    is_match = True
                elif linked_path + '.md' in target_names:
                    is_match = True
                
                if is_match:
                    alias = match.group(3)
                    link_text = alias.strip() if alias else match.group(1).strip()
                    
                    backlink_info = {
                        'source_path': note_path,
                        'link_text': link_text,
                        'link_type': 'wiki'
                    }
                    
                    if include_context:
                        backlink_info['context'] = get_link_context(content, match, context_length)
                    
                    note_backlinks.append(backlink_info)
            
            # Check for markdown-style links
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
                    
                    note_backlinks.append(backlink_info)
            
            return note_backlinks
            
        except Exception:
            return []
    
    # Process in batches
    for i in range(0, len(all_note_paths), batch_size):
        batch = all_note_paths[i:i + batch_size]
        batch_results = await asyncio.gather(*[check_note_for_backlinks(np) for np in batch])
        
        for note_backlinks in batch_results:
            backlinks.extend(note_backlinks)
    
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
    Get all links from a specific note (optimized version).
    
    This tool extracts all outgoing links from a note, helping understand
    what other notes and resources it references.
    
    Args:
        path: Path to the source note
        check_validity: Whether to check if linked notes exist
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing:
        - source_note: The note containing the links
        - link_count: Number of links found
        - links: List of link information including:
          - path: The linked note path
          - display_text: The display text of the link
          - type: 'wiki' or 'markdown'
          - exists: Whether the linked note exists (if check_validity=True)
          - actual_path: The actual path if different from link path
          
    Example:
        {
            "source_note": "Daily/2024-01-15.md",
            "link_count": 5,
            "links": [
                {
                    "path": "Projects/My Project.md",
                    "display_text": "My Project",
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
    note = await api.get_note(path)
    if not note:
        raise FileNotFoundError(f"Note not found: {path}")
    
    content = note.content
    
    # Extract all links
    links = extract_links_from_content(content)
    
    # Check validity if requested - in batch!
    if check_validity:
        if ctx:
            ctx.info(f"Checking validity of {len(links)} links...")
        links = await check_links_validity_batch(api, links)
    
    if ctx:
        ctx.info(f"Found {len(links)} outgoing links")
    
    return {
        'source_note': path,
        'link_count': len(links),
        'links': links
    }


async def find_broken_links(
    directory: Optional[str] = None,
    single_note: Optional[str] = None,
    ctx=None
) -> dict:
    """
    Find all broken links in the vault, a specific directory, or a single note (optimized version).
    
    This tool identifies links pointing to non-existent notes, helping maintain
    vault integrity. Broken links often occur after renaming or deleting notes.
    
    Args:
        directory: Specific directory to check (optional, defaults to entire vault)
        single_note: Check only this specific note (optional)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing:
        - broken_link_count: Total number of broken links
        - affected_notes: Number of notes containing broken links
        - broken_links: List of broken link details including:
          - source_path: Note containing the broken link
          - broken_link: The path that doesn't exist
          - link_text: The display text of the link
          - link_type: 'wiki' or 'markdown'
          
    Example:
        {
            "broken_link_count": 3,
            "affected_notes": 2,
            "broken_links": [
                {
                    "source_path": "Daily/2024-01-15.md",
                    "broken_link": "Projects/Old Project.md",
                    "link_text": "Old Project",
                    "link_type": "wiki"
                }
            ]
        }
    """
    if ctx:
        if single_note:
            scope = f"note: {single_note}"
        elif directory:
            scope = f"directory: {directory}"
        else:
            scope = "entire vault"
        ctx.info(f"Checking for broken links in {scope}")
    
    api = ObsidianAPI()
    
    # Get notes to check
    notes_to_check = []
    if single_note:
        notes_to_check = [single_note]
    else:
        # Build index to get all notes
        notes_index = await build_vault_notes_index(api)
        all_notes = list(set(notes_index.values()))  # Get unique paths
        
        if directory:
            # Filter to directory
            notes_to_check = [n for n in all_notes if n.startswith(directory + '/') or n.startswith(directory)]
        else:
            notes_to_check = all_notes
    
    if ctx:
        ctx.info(f"Checking {len(notes_to_check)} notes...")
    
    # Collect all links from all notes
    all_links_by_note = {}
    batch_size = 10
    
    async def get_note_links(note_path: str) -> Tuple[str, List[dict]]:
        """Get all links from a note."""
        try:
            note = await api.get_note(note_path)
            if not note:
                return note_path, []
            return note_path, extract_links_from_content(note.content)
        except Exception:
            return note_path, []
    
    # Process notes in batches
    for i in range(0, len(notes_to_check), batch_size):
        batch = notes_to_check[i:i + batch_size]
        batch_results = await asyncio.gather(*[get_note_links(np) for np in batch])
        
        for note_path, links in batch_results:
            if links:
                all_links_by_note[note_path] = links
    
    # Get all unique link paths
    all_link_paths = set()
    for links in all_links_by_note.values():
        for link in links:
            all_link_paths.add(link['path'])
    
    if ctx:
        ctx.info(f"Checking validity of {len(all_link_paths)} unique links...")
    
    # Check which links exist - in one batch!
    found_paths = await find_notes_by_names(api, list(all_link_paths))
    
    # Find broken links
    broken_links = []
    affected_notes_set = set()
    
    for note_path, links in all_links_by_note.items():
        for link in links:
            if not found_paths.get(link['path']):
                broken_link_info = {
                    'source_path': note_path,
                    'broken_link': link['path'],
                    'link_text': link['display_text'],
                    'link_type': link['type']
                }
                broken_links.append(broken_link_info)
                affected_notes_set.add(note_path)
    
    if ctx:
        ctx.info(f"Found {len(broken_links)} broken links in {len(affected_notes_set)} notes")
    
    # Sort broken links by source path
    broken_links.sort(key=lambda x: x['source_path'])
    
    result = {
        'broken_link_count': len(broken_links),
        'affected_notes': len(affected_notes_set),
        'broken_links': broken_links
    }
    
    # Add context about what was checked
    if single_note:
        result['checked'] = 'single_note'
        result['note'] = single_note
    else:
        result['checked'] = 'directory'
        result['directory'] = directory or '/'
    
    return result