"""Tool modules for Obsidian MCP server."""

from .note_management import (
    read_note,
    create_note,
    update_note,
    delete_note,
)
from .search_discovery import (
    search_notes,
    list_notes,
)
from .organization import (
    move_note,
    add_tags,
    remove_tags,
    get_note_info,
)

__all__ = [
    # Note management
    "read_note",
    "create_note", 
    "update_note",
    "delete_note",
    # Search and discovery
    "search_notes",
    "list_notes",
    # Organization
    "move_note",
    "add_tags",
    "remove_tags",
    "get_note_info",
]