"""Validation utilities for Obsidian MCP server."""

import os
from typing import Optional
from ..constants import MARKDOWN_EXTENSIONS


def validate_note_path(path: str) -> tuple[bool, Optional[str]]:
    """
    Validate a note path.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path cannot be empty"
    
    # Check for path traversal attempts
    if ".." in path or path.startswith("/"):
        return False, "Path cannot contain '..' or start with '/'"
    
    # Check for invalid characters
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
    for char in invalid_chars:
        if char in path:
            return False, f"Path contains invalid character: {char}"
    
    return True, None


def sanitize_path(path: str) -> str:
    """
    Sanitize a path for use with Obsidian.
    
    Args:
        path: Path to sanitize
        
    Returns:
        Sanitized path
    """
    # Remove leading/trailing slashes and whitespace
    path = path.strip().strip("/")
    
    # Ensure .md extension
    if not any(path.endswith(ext) for ext in MARKDOWN_EXTENSIONS):
        path += ".md"
    
    return path


def is_markdown_file(path: str) -> bool:
    """Check if a path points to a markdown file."""
    return any(path.lower().endswith(ext) for ext in MARKDOWN_EXTENSIONS)