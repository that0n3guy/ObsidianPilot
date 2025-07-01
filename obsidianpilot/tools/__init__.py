"""Tool modules for Obsidian MCP server."""

from .note_management import (
    read_note,
    create_note,
    update_note,
    delete_note,
    edit_note_section,
    edit_note_content,
)
from .search_discovery import (
    search_by_date,
    search_by_regex,
    search_by_property,
    list_notes,
    list_folders,
)
from .organization import (
    move_note,
    create_folder,
    move_folder,
    add_tags,
    update_tags,
    remove_tags,
    get_note_info,
    list_tags,
)
from .link_management import (
    get_backlinks,
    get_outgoing_links,
    find_broken_links,
)
from .image_management import (
    read_image,
)
from .view_note_images import (
    view_note_images,
)
from .fast_search import (
    search_notes,
)

__all__ = [
    # Note management
    "read_note",
    "create_note", 
    "update_note",
    "delete_note",
    "edit_note_section",
    "edit_note_content",
    # Search and discovery
    "search_notes",
    "search_by_date",
    "search_by_regex",
    "search_by_property",
    "list_notes",
    "list_folders",
    # Organization
    "move_note",
    "create_folder",
    "move_folder",
    "add_tags",
    "update_tags",
    "remove_tags",
    "get_note_info",
    "list_tags",
    # Link management
    "get_backlinks",
    "get_outgoing_links",
    "find_broken_links",
    # Image management
    "read_image",
    "view_note_images",
]