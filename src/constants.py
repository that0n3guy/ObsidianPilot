"""Constants for Obsidian MCP server."""

# Obsidian REST API configuration
OBSIDIAN_BASE_URL = "https://localhost:27124"
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_SEARCH_CONTEXT_LENGTH = 100
DEFAULT_LIST_RECURSIVE = True

# API Endpoints
ENDPOINTS = {
    "vault": "/vault/",
    "vault_path": "/vault/{path}",
    "search": "/search/",
    "search_simple": "/search/simple/",
}

# File extensions
MARKDOWN_EXTENSIONS = {".md", ".markdown"}

# Error messages
ERROR_MESSAGES = {
    "connection_failed": "Failed to connect to Obsidian. Ensure Obsidian is running with the Local REST API plugin enabled.",
    "note_not_found": "Note not found at path: {path}",
    "invalid_path": "Invalid note path: {path}",
    "overwrite_protection": "Note already exists at {path}. Set overwrite=true to replace it.",
    "api_key_missing": "OBSIDIAN_REST_API_KEY environment variable not set",
}