"""Enhanced validation utilities with constraint checking."""

import re
from typing import List, Tuple, Optional, Any
from ..constants import MARKDOWN_EXTENSIONS, ERROR_MESSAGES


class ValidationError(ValueError):
    """Custom validation error with detailed messages."""
    pass


def validate_note_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a note path with comprehensive checks.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path cannot be empty"
    
    # Check length (matching our schema constraint)
    if len(path) > 255:
        return False, ERROR_MESSAGES["path_too_long"].format(length=len(path))
    
    # Check pattern (must not start with /)
    if path.startswith("/"):
        return False, ERROR_MESSAGES["invalid_path"].format(path=path)
    
    # Check for path traversal attempts
    if ".." in path:
        return False, ERROR_MESSAGES["invalid_path"].format(path=path)
    
    # Check extension
    if not any(path.endswith(ext) for ext in MARKDOWN_EXTENSIONS):
        return False, ERROR_MESSAGES["invalid_path"].format(path=path)
    
    # Check for invalid characters
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
    for char in invalid_chars:
        if char in path:
            return False, ERROR_MESSAGES["invalid_path"].format(path=path)
    
    # Check pattern matches our schema
    pattern = r"^[^/].*\.md$"
    if not re.match(pattern, path):
        return False, ERROR_MESSAGES["invalid_path"].format(path=path)
    
    return True, None


def validate_search_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a search query.
    
    Args:
        query: Search query to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, ERROR_MESSAGES["empty_search_query"]
    
    # Check length constraint
    if len(query) > 500:
        return False, f"Search query too long: {len(query)} characters (max: 500)"
    
    return True, None


def validate_context_length(length: int) -> Tuple[bool, Optional[str]]:
    """
    Validate context length parameter.
    
    Args:
        length: Context length to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if length < 10 or length > 500:
        return False, ERROR_MESSAGES["invalid_context_length"].format(length=length)
    
    return True, None


def validate_date_search_params(
    date_type: str, 
    days_ago: int, 
    operator: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate date search parameters.
    
    Args:
        date_type: Type of date to search by
        days_ago: Number of days to look back
        operator: Search operator
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate date_type
    if date_type not in ["created", "modified"]:
        return False, ERROR_MESSAGES["invalid_date_type"].format(date_type=date_type)
    
    # Validate operator
    if operator not in ["within", "exactly"]:
        return False, ERROR_MESSAGES["invalid_operator"].format(operator=operator)
    
    # Validate days_ago
    if days_ago < 0:
        return False, ERROR_MESSAGES["negative_days"].format(days=days_ago)
    
    if days_ago > 365:
        return False, f"Days ago too large: {days_ago} (max: 365). Use smaller values or implement year-based search."
    
    return True, None


def validate_tags(tags: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a list of tags.
    
    Args:
        tags: List of tags to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not tags:
        return False, ERROR_MESSAGES["invalid_tags"]
    
    # Check each tag
    cleaned_tags = []
    for tag in tags:
        # Remove # prefix and strip whitespace
        cleaned = tag.lstrip("#").strip()
        if not cleaned:
            return False, ERROR_MESSAGES["invalid_tags"]
        cleaned_tags.append(cleaned)
    
    # Check count constraints
    if len(cleaned_tags) > 50:
        return False, f"Too many tags: {len(cleaned_tags)} (max: 50). Consider organizing with folders instead."
    
    return True, None


def validate_directory_path(path: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a directory path for listing.
    
    Args:
        path: Directory path to validate (can be None)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if path is None:
        return True, None
    
    # Check length
    if len(path) > 255:
        return False, f"Directory path too long: {len(path)} characters (max: 255)"
    
    # Check pattern (must not start or end with /)
    if path.startswith("/"):
        return False, f"Directory path cannot start with '/': {path}"
    
    if path.endswith("/"):
        return False, f"Directory path cannot end with '/': {path}"
    
    # Check for path traversal
    if ".." in path:
        return False, f"Directory path cannot contain '..': {path}"
    
    return True, None


def validate_content(content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate note content.
    
    Args:
        content: Note content to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check size constraint (1MB limit)
    if len(content) > 1_000_000:
        return False, f"Content too large: {len(content)} characters (max: 1,000,000). Consider splitting into multiple notes."
    
    return True, None


# Validation decorators for use in tools
def validate_params(validation_func):
    """Decorator to validate parameters before calling a function."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Run validation
            is_valid, error = validation_func(*args, **kwargs)
            if not is_valid:
                raise ValidationError(error)
            
            # Call the original function
            return await func(*args, **kwargs)
        return wrapper
    return decorator