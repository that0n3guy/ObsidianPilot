# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that enables AI assistants to interact with Obsidian vaults through the Local REST API plugin. The server provides tools for reading, creating, searching, and listing notes in Obsidian.

## Key Architecture

The server uses FastMCP framework and implements 4 main tools:
- `read_note`: Read content of a specific note by path
- `create_note`: Create/update notes with overwrite protection
- `search_notes`: Search notes using Obsidian's search syntax
- `list_notes`: List notes recursively or by directory

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

- `src/server.py`: Main MCP server implementation with all tool handlers
- Authentication handled via API key in request headers
- Uses httpx for async HTTP operations
- Error handling includes proper MCP error responses with details