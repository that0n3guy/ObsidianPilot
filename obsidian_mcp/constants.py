"""Constants for Obsidian MCP server."""

# Obsidian REST API configuration
OBSIDIAN_BASE_URL = "http://127.0.0.1:27123"
DEFAULT_TIMEOUT = 10  # seconds - reduced for local API
DEFAULT_SEARCH_CONTEXT_LENGTH = 100
DEFAULT_LIST_RECURSIVE = True

# API Endpoints
ENDPOINTS = {
    "vault": "/vault/",
    "vault_path": "/vault/{path}",  # No trailing slash for individual files
    "search": "/search/",
    "search_simple": "/search/simple/",
}

# File extensions
MARKDOWN_EXTENSIONS = {".md", ".markdown"}

# Error messages - Actionable and specific
ERROR_MESSAGES = {
    "connection_failed": (
        "Cannot connect to Obsidian REST API at {url}. "
        "To fix: 1) Ensure Obsidian is running, 2) Enable the Local REST API plugin in Obsidian settings, "
        "3) Verify the API is running on port {port}, 4) Check if your firewall is blocking local connections. "
        "Note: You can override the URL with OBSIDIAN_API_URL environment variable"
    ),
    "note_not_found": (
        "Note not found at path: '{path}'. "
        "To fix: 1) Check if the path is correct (case-sensitive), 2) Ensure the note exists in your vault, "
        "3) Use list_notes to see available notes in the directory"
    ),
    "invalid_path": (
        "Invalid note path: '{path}'. "
        "Valid paths must: 1) End with .md or .markdown, 2) Use forward slashes (e.g., 'folder/note.md'), "
        "3) Not contain '..' or start with '/', 4) Not exceed 255 characters. "
        "Example: 'Daily/2024-01-15.md' or 'Projects/My Project.md'"
    ),
    "overwrite_protection": (
        "Note already exists at '{path}'. "
        "To proceed: 1) Set overwrite=true to replace the existing note, "
        "2) Use update_note to modify the existing note, "
        "3) Choose a different path for the new note"
    ),
    "api_key_missing": (
        "OBSIDIAN_REST_API_KEY environment variable not set. "
        "To fix: 1) Open Obsidian settings > Community plugins > Local REST API, "
        "2) Copy the API key shown there, "
        "3) Set the environment variable: export OBSIDIAN_REST_API_KEY='your-key-here'"
    ),
    "empty_search_query": (
        "Search query cannot be empty. "
        "Valid queries: 1) Keywords: 'machine learning', "
        "2) Tags: 'tag:#project', 3) Paths: 'path:Daily/', "
        "4) Combined: 'tag:#urgent TODO'"
    ),
    "invalid_date_type": (
        "Invalid date_type: '{date_type}'. "
        "Must be either 'created' or 'modified'. "
        "Use 'created' to find notes by creation date, 'modified' for last edit date"
    ),
    "invalid_operator": (
        "Invalid operator: '{operator}'. "
        "Must be either 'within' or 'exactly'. "
        "Use 'within' for date ranges (e.g., last 7 days), 'exactly' for specific days ago"
    ),
    "negative_days": (
        "Invalid days_ago: {days}. "
        "Must be a positive number (0 or greater). "
        "Use 0 for today, 1 for yesterday, 7 for last week, etc."
    ),
    "invalid_tags": (
        "Invalid tags provided. "
        "Tags must be non-empty strings without the # prefix. "
        "Example: ['project', 'urgent', 'review'] not ['#project', '', ' ']"
    ),
    "path_too_long": (
        "Path too long: {length} characters (max: 255). "
        "To fix: Use shorter folder/file names or reduce nesting depth"
    ),
    "invalid_context_length": (
        "Invalid context_length: {length}. "
        "Must be between 10 and 500 characters. "
        "Use smaller values for brief previews, larger for more context"
    ),
    "invalid_sort_by": (
        "Invalid sort_by parameter: '{value}'. "
        "Must be either 'name' (alphabetical) or 'count' (by usage). "
        "Default is 'name' for alphabetical sorting"
    ),
    "tag_collection_failed": (
        "Failed to collect tags from vault: {error}. "
        "This may happen if: 1) The Obsidian API is not responding, "
        "2) There are permission issues with some notes, "
        "3) The vault is very large (try again or use search_notes with specific tags)"
    ),
    "folder_listing_failed": (
        "Failed to list folders in '{directory}': {error}. "
        "To fix: 1) Verify the directory path is correct, "
        "2) Check if the directory exists using list_notes, "
        "3) Ensure you have permission to access this directory"
    ),
    "folder_move_failed": (
        "Failed to move folder '{source}' to '{destination}': {error}. "
        "To fix: 1) Verify both folder paths are correct, "
        "2) Ensure the source folder exists and contains notes, "
        "3) Check that destination is not a subfolder of source, "
        "4) Verify you have permission to create/delete notes"
    ),
}