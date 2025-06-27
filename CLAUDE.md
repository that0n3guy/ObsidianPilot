# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ObsidianPilot is an enhanced MCP (Model Context Protocol) server that enables AI assistants to interact with Obsidian vaults through direct filesystem access. The server provides tools for reading, creating, searching, and managing notes in Obsidian with blazing-fast performance and token-efficient editing capabilities.

## Key Architecture

The server uses FastMCP framework with a modular structure:

### File Organization
```
obsidian_mcp/
├── server.py           # Main entry point, tool registration
├── tools/              # Tool implementations
│   ├── note_management.py    # CRUD operations + token-efficient editing
│   ├── search_discovery.py   # Search and navigation tools
│   ├── organization.py       # Tags, moves, metadata management
│   ├── link_management.py    # Backlinks, outgoing links, broken links
│   ├── image_management.py   # Image viewing and analysis
│   └── view_note_images.py   # Extract images from notes
├── models/             # Pydantic models for validation
│   └── obsidian.py    # Note, SearchResult, VaultItem models
├── utils/              # Shared utilities
│   ├── filesystem.py        # Direct filesystem access
│   ├── persistent_index.py  # SQLite search indexing
│   ├── validators.py        # Path validation, sanitization
│   └── validation.py        # Parameter validation
└── constants.py       # Error messages and constants
```

### Core Tools

#### Note Management
- `read_note`: Read content and metadata of a specific note
- `create_note`: Create new notes with overwrite protection
- `update_note`: Modify existing notes with optional create
- `delete_note`: Remove notes from vault
- `edit_note_section`: **NEW** - Token-efficient section editing with 5 operations
- `edit_note_content`: **NEW** - Precise text search and replace

#### Search & Discovery
- `search_notes`: Search using Obsidian's syntax with context
- `search_by_date`: Find notes by creation/modification date
- `search_by_regex`: Advanced pattern matching with regular expressions
- `search_by_property`: Query notes by frontmatter properties
- `list_notes`: Browse vault structure recursively or by directory
- `list_folders`: List folder structure

#### Organization & Links
- `move_note`: Move notes with automatic link updates
- `add_tags`, `update_tags`, `remove_tags`: Tag management
- `get_backlinks`, `get_outgoing_links`: Link analysis
- `find_broken_links`: Identify broken links for maintenance

#### Images
- `read_image`: View images with automatic resizing
- `view_note_images`: Extract and analyze images from notes

All operations work through direct filesystem access with persistent SQLite indexing for blazing-fast performance.

## Development Commands

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m obsidian_mcp.server

# Run tests
python tests/run_tests.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector -e OBSIDIAN_VAULT_PATH=/path/to/vault python -m obsidian_mcp.server
```

## Important Configuration

- Requires `OBSIDIAN_VAULT_PATH` environment variable pointing to your Obsidian vault
- Works offline - no plugins required, Obsidian doesn't need to be running
- Persistent SQLite index stored in `.obsidian/mcp-search-index.db` for fast searches

## Token-Efficient Editing (New in v2.0.3)

The server now includes advanced editing capabilities that minimize token usage:

### `edit_note_section` - Section-Based Editing
Edit specific markdown sections without reading entire files:
- **insert_after**: Add content after section heading
- **insert_before**: Add content before section heading  
- **replace_section**: Replace entire section including heading
- **append_to_section**: Add content at end of section
- **edit_heading**: Change just the heading text

### `edit_note_content` - Precise Text Replacement
Replace specific text without full file context:
- First or all occurrence replacement
- Perfect for values, typos, frontmatter updates
- Exact text matching

### Key Benefits
- **Reduced token usage**: Only target content, not entire files
- **Frontmatter preservation**: Automatically maintains YAML structure
- **Precise operations**: Change only what needs changing
- **Performance**: Faster than full file rewrites

## Code Structure

### Design Principles
- **Single responsibility**: Each module has one clear purpose
- **Type safety**: Pydantic models for all complex data structures
- **Clear naming**: Verb-object pattern for tools (read_note, create_note)
- **Progressive disclosure**: Simple interfaces with optional complexity
- **Comprehensive error handling**: Specific, actionable error messages

### Key Components
- `ObsidianAPI`: Centralized REST API client with consistent error handling
- Validators ensure path safety and prevent directory traversal
- Models provide type-safe data structures for all Obsidian entities
- Tools follow consistent patterns for parameters and responses