# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that enables AI assistants to interact with Obsidian vaults through the Local REST API plugin. The server provides tools for reading, creating, searching, and listing notes in Obsidian.

## Key Architecture

The server uses FastMCP framework with a modular structure:

### File Organization
```
src/
├── server.py           # Main entry point, tool registration
├── tools/              # Tool implementations
│   ├── note_management.py    # CRUD operations (read, create, update, delete)
│   ├── search_discovery.py   # Search and navigation tools
│   └── organization.py       # Tags, moves, metadata (future)
├── models/             # Pydantic models for validation
│   └── obsidian.py    # Note, SearchResult, VaultItem models
├── utils/              # Shared utilities
│   ├── obsidian_api.py      # REST API client wrapper
│   └── validators.py        # Path validation, sanitization
└── constants.py       # API endpoints, defaults, error messages
```

### Core Tools
- `read_note`: Read content and metadata of a specific note
- `create_note`: Create new notes with overwrite protection
- `update_note`: Modify existing notes with optional create
- `delete_note`: Remove notes from vault
- `search_notes`: Search using Obsidian's syntax with context
- `list_notes`: Browse vault structure recursively or by directory

All communication with Obsidian happens through async HTTP requests to `https://localhost:27124` using the Local REST API plugin.

## Development Commands

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m src.server

# Run tests
python tests/test_server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector -e OBSIDIAN_REST_API_KEY=$OBSIDIAN_REST_API_KEY python -m src.server
```

## Important Configuration

- Requires `OBSIDIAN_REST_API_KEY` environment variable
- Obsidian must be running with Local REST API plugin enabled
- The server suppresses SSL warnings for self-signed certificates

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