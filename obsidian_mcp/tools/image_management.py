"""Image management tools for Obsidian MCP server."""

import base64
from typing import Optional, Union, Dict, Any
from fastmcp import Context
from fastmcp.utilities.types import Image
from ..utils.filesystem import get_vault
from ..utils import validate_note_path, sanitize_path
from ..constants import ERROR_MESSAGES


async def read_image(
    path: str,
    include_metadata: bool = False,
    max_width: int = 1600,
    ctx: Optional[Context] = None
) -> Union[Image, Dict[str, Any]]:
    """
    Read an image file from the Obsidian vault and return it as an Image object.
    
    Use this tool when you need to retrieve image files from the vault. The image
    is returned as an Image object that can be displayed directly in MCP clients.
    Images larger than max_width are automatically resized to prevent memory issues.
    
    Args:
        path: Path to the image file relative to vault root (e.g., "attachments/screenshot.png")
        include_metadata: Whether to include file metadata (returns dict with image and metadata)
        max_width: Maximum width for automatic resizing in pixels (default: 1600)
        ctx: MCP context for progress reporting
        
    Returns:
        If include_metadata is False: Image object for direct display
        If include_metadata is True: Dictionary containing image object and metadata
        
    Example:
        >>> # For display only
        >>> await read_image("images/diagram.png")
        <Image object>
        
        >>> # With metadata
        >>> await read_image("images/diagram.png", include_metadata=True)
        {
            "image": <Image object>,
            "path": "images/diagram.png",
            "mime_type": "image/png",
            "size": 1234,
            "resized": true,
            "dimensions": {
                "original": {"width": 2400, "height": 1800},
                "resized": {"width": 1200, "height": 900}
            }
        }
    """
    # Validate path (reuse existing validation but allow image extensions)
    if not path:
        raise ValueError("Path cannot be empty")
    
    # Check for common image extensions
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'}
    ext = path.lower().split('.')[-1] if '.' in path else ''
    if f'.{ext}' not in valid_extensions:
        raise ValueError(f"Invalid image file extension. Supported: {', '.join(valid_extensions)}")
    
    # Don't sanitize path for images - it adds .md extension
    
    if ctx:
        ctx.info(f"Reading image: {path}")
    
    vault = get_vault()
    
    try:
        image_data = await vault.read_image(path, max_width=max_width)
    except FileNotFoundError:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    # Convert base64 content back to bytes for Image object
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
    
    if include_metadata:
        # If metadata is requested, return both Image and metadata in a dict
        result = {
            "image": Image(data=image_bytes, format=format_type),
            "path": image_data["path"],
            "mime_type": image_data["mime_type"],
            "size": image_data["size"]
        }
        
        if "original_size" in image_data:
            result["original_size"] = image_data["original_size"]
        if "resized" in image_data:
            result["resized"] = image_data["resized"]
        if "dimensions" in image_data:
            result["dimensions"] = image_data["dimensions"]
            
        return result
    else:
        # Return just the Image object for display
        return Image(data=image_bytes, format=format_type)