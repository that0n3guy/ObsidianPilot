"""Validation utilities for Obsidian MCP server."""

import os
from typing import Optional
from ..constants import MARKDOWN_EXTENSIONS, ERROR_MESSAGES


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
    
    # Check length
    if len(path) > 255:
        return False, ERROR_MESSAGES["path_too_long"].format(length=len(path))
    
    # Check for path traversal attempts
    if ".." in path or path.startswith("/"):
        return False, ERROR_MESSAGES["invalid_path"].format(path=path)
    
    # Check extension
    if not any(path.endswith(ext) for ext in MARKDOWN_EXTENSIONS):
        return False, ERROR_MESSAGES["invalid_path"].format(path=path)
    
    # Check for invalid characters
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
    for char in invalid_chars:
        if char in path:
            return False, ERROR_MESSAGES["invalid_path"].format(path=path)
    
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