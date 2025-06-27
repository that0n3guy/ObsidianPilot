"""Tool for viewing images embedded in notes."""

import re
import base64
from typing import List, Optional
from fastmcp import Context
from fastmcp.utilities.types import Image
from ..utils.filesystem import get_vault
from ..utils import validate_note_path, sanitize_path
from ..constants import ERROR_MESSAGES


async def view_note_images(
    path: str,
    image_index: Optional[int] = None,
    max_width: int = 1600,
    ctx: Optional[Context] = None
) -> List[Image]:
    """
    Extract and display images embedded in a note.
    
    Use this tool to view images that are referenced within a note's content.
    This is separate from read_note to ensure proper image display in MCP clients.
    
    Args:
        path: Path to the note containing images
        image_index: Optional specific image index to display (0-based)
        max_width: Maximum width for automatic resizing in pixels (default: 800)
        ctx: MCP context for progress reporting
        
    Returns:
        List of Image objects from the note (or single image if index specified)
        
    Example:
        >>> # View all images in a note
        >>> await view_note_images("Projects/Design.md")
        [<Image>, <Image>, ...]
        
        >>> # View specific image by index
        >>> await view_note_images("Projects/Design.md", image_index=0)
        [<Image>]
    """
    # Validate path
    is_valid, error_msg = validate_note_path(path)
    if not is_valid:
        raise ValueError(f"Invalid path: {error_msg}")
    
    path = sanitize_path(path)
    
    if ctx:
        ctx.info(f"Extracting images from note: {path}")
    
    vault = get_vault()
    
    # Read the note to get its content
    try:
        note = await vault.read_note(path)
    except FileNotFoundError:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Extract image references
    wiki_pattern = r'!\[\[([^]]+\.(?:png|jpg|jpeg|gif|webp|svg|bmp|ico))\]\]'
    markdown_pattern = r'!\[[^\]]*\]\(([^)]+\.(?:png|jpg|jpeg|gif|webp|svg|bmp|ico))\)'
    
    image_paths = []
    
    # Find wiki-style embeds
    for match in re.finditer(wiki_pattern, note.content, re.IGNORECASE):
        image_paths.append(match.group(1))
    
    # Find markdown-style embeds
    for match in re.finditer(markdown_pattern, note.content, re.IGNORECASE):
        image_paths.append(match.group(1))
    
    if not image_paths:
        if ctx:
            ctx.info("No images found in this note")
        return []
    
    if ctx:
        ctx.info(f"Found {len(image_paths)} image(s) in note")
    
    # If specific index requested, validate it
    if image_index is not None:
        if image_index < 0 or image_index >= len(image_paths):
            raise ValueError(f"Invalid image index {image_index}. Note contains {len(image_paths)} images (0-{len(image_paths)-1})")
        image_paths = [image_paths[image_index]]
    
    # Load and convert images to Image objects
    images = []
    
    for i, image_ref in enumerate(image_paths):
        try:
            if ctx:
                ctx.info(f"Loading image {i+1}/{len(image_paths)}: {image_ref}")
            
            # Try to read the image directly
            try:
                image_data = await vault.read_image(image_ref, max_width=max_width)
            except FileNotFoundError:
                # If not found at direct path, search for it
                filename = image_ref.split('/')[-1]
                found_path = await vault.find_image(filename)
                if found_path:
                    if ctx:
                        ctx.info(f"Found image at: {found_path}")
                    image_data = await vault.read_image(found_path, max_width=max_width)
                else:
                    if ctx:
                        ctx.info(f"Could not find image: {image_ref}")
                    continue
            
            # Convert to Image object
            image_bytes = base64.b64decode(image_data["content"])
            
            # Extract format from mime type
            mime_to_format = {
                "image/png": "png",
                "image/jpeg": "jpeg",
                "image/jpg": "jpeg",
                "image/gif": "gif",
                "image/webp": "webp",
                "image/svg+xml": "svg",
                "image/bmp": "bmp",
                "image/x-icon": "ico"
            }
            format_type = mime_to_format.get(image_data["mime_type"], "png")
            
            images.append(Image(data=image_bytes, format=format_type))
            
        except Exception as e:
            if ctx:
                ctx.info(f"Error loading image {image_ref}: {str(e)}")
            continue
    
    return images