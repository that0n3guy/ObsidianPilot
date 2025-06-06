# Obsidian MCP Server

A Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with your Obsidian vault. This server provides tools for reading, creating, searching, and managing notes in Obsidian through the Local REST API plugin.

## Features

- 📖 **Read notes** from your Obsidian vault
- ✍️ **Create and update notes** with automatic overwrite protection
- 🔍 **Search notes** using Obsidian's search functionality
- 📁 **List notes** recursively or by directory
- 🏷️ **Manage tags** in note frontmatter
- 📊 **Get note statistics** including word count and links
- 🔒 **Secure communication** with API key authentication
- 🧪 **Comprehensive testing** suite with unit, integration, and live tests

## Prerequisites

- **Obsidian** with the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin installed and enabled
- **Python 3.10+** installed on your system
- **Node.js** (optional, for running MCP Inspector)

## Installation

### Quick Start (Development)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/natestrong/obsidian-mcp
   cd obsidian-mcp
   ```

2. **Set up Python environment:**
   ```bash
   # Using pyenv (recommended)
   pyenv virtualenv 3.12.9 obsidian-mcp
   pyenv activate obsidian-mcp
   
   # Or using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Obsidian Local REST API:**
   - Install the Local REST API plugin in Obsidian
   - Enable the plugin in Obsidian settings
   - Copy the API key from the plugin settings
   - Note the port number (default: 27124)

5. **Configure environment variables:**
   ```bash
   export OBSIDIAN_REST_API_KEY="your-api-key-here"
   export OBSIDIAN_API_URL="https://localhost:27124"  # if not using default
   ```

## Project Structure

```
obsidian-mcp/
├── src/
│   ├── server.py           # Main entry point, tool registration
│   ├── tools/              # Tool implementations
│   │   ├── note_management.py    # CRUD operations
│   │   ├── search_discovery.py   # Search and navigation
│   │   └── organization.py       # Tags, moves, metadata
│   ├── models/             # Pydantic models for validation
│   │   └── obsidian.py    # Note, SearchResult, VaultItem models
│   ├── utils/              # Shared utilities
│   │   ├── obsidian_api.py      # REST API client wrapper
│   │   └── validators.py        # Path validation, sanitization
│   └── constants.py       # API endpoints, defaults, error messages
├── tests/
│   ├── run_tests.py       # Smart test runner
│   ├── test_unit.py       # Unit tests with mocks
│   ├── test_integration.py # Integration tests
│   ├── test_live.py       # Live API tests
│   ├── test_comprehensive.py # Full workflow validation
│   └── test_data_validation.py # Return value testing
├── docs/                  # Additional documentation
├── requirements.txt       # Python dependencies
├── CLAUDE.md             # Instructions for Claude Code
└── README.md
```

## Available Tools

### Note Management

#### `read_note`
Read the content and metadata of a specific note.

**Parameters:**
- `path`: Path to the note (e.g., "Daily/2024-01-15.md")

**Returns:**
```json
{
  "path": "Daily/2024-01-15.md",
  "content": "# Daily Note\n\nContent here...",
  "metadata": {
    "tags": ["daily", "journal"],
    "aliases": [],
    "frontmatter": {}
  }
}
```

#### `create_note`
Create a new note or update an existing one.

**Parameters:**
- `path`: Path where the note should be created
- `content`: Markdown content of the note
- `overwrite` (default: `false`): Whether to overwrite existing notes

#### `update_note`
Update the content of an existing note.

**Parameters:**
- `path`: Path to the note to update
- `content`: New markdown content
- `create_if_not_exists` (default: `false`): Create if doesn't exist

#### `delete_note`
Delete a note from the vault.

**Parameters:**
- `path`: Path to the note to delete

### Search and Discovery

#### `search_notes`
Search for notes containing specific text.

**Parameters:**
- `query`: Search query (supports Obsidian search syntax)
- `context_length` (default: `100`): Number of characters to show around matches

**Note:** Search functionality may have connectivity issues with some REST API configurations.

#### `list_notes`
List notes in your vault with optional recursive traversal.

**Parameters:**
- `directory` (optional): Specific directory to list (e.g., "Daily", "Projects")
- `recursive` (default: `true`): List all notes recursively

**Returns:**
```json
{
  "directory": "Daily",
  "recursive": true,
  "count": 365,
  "notes": [
    {"path": "Daily/2024-01-01.md", "name": "2024-01-01.md"},
    {"path": "Daily/2024-01-02.md", "name": "2024-01-02.md"}
  ]
}
```

### Organization

#### `move_note`
Move a note to a new location.

**Parameters:**
- `source_path`: Current path of the note
- `destination_path`: New path for the note
- `update_links` (default: `true`): Update links in other notes (future enhancement)

#### `add_tags`
Add tags to a note's frontmatter.

**Parameters:**
- `path`: Path to the note
- `tags`: List of tags to add (without # prefix)

#### `remove_tags`
Remove tags from a note's frontmatter.

**Parameters:**
- `path`: Path to the note
- `tags`: List of tags to remove

#### `get_note_info`
Get metadata and statistics about a note without retrieving its full content.

**Parameters:**
- `path`: Path to the note

**Returns:**
```json
{
  "path": "Projects/AI Research.md",
  "exists": true,
  "metadata": {
    "tags": ["ai", "research"],
    "aliases": [],
    "frontmatter": {}
  },
  "stats": {
    "size_bytes": 4523,
    "word_count": 823,
    "link_count": 12
  }
}
```

## Testing

### Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test types
python tests/run_tests.py unit         # Unit tests (requires pytest)
python tests/run_tests.py integration  # Integration tests (requires pytest)  
python tests/run_tests.py live         # Live tests with real Obsidian

# Run individual test files
python tests/test_comprehensive.py     # Full workflow test
python tests/test_data_validation.py   # Data structure validation
```

### Testing with MCP Inspector

1. **Ensure Obsidian is running** with the Local REST API plugin enabled

2. **Run the MCP Inspector:**
   ```bash
   npx @modelcontextprotocol/inspector python -m src.server
   ```

3. **Open the Inspector UI** at `http://localhost:5173`

4. **Test the tools** interactively with your actual vault

## Integration with Claude Desktop

### Configuration

1. **Add to Claude Desktop configuration:**

   Edit your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "/path/to/python",
         "args": ["-m", "src.server"],
         "cwd": "/path/to/obsidian-mcp",
         "env": {
           "PYTHONPATH": "/path/to/obsidian-mcp",
           "OBSIDIAN_REST_API_KEY": "your-api-key-here",
           "OBSIDIAN_API_URL": "https://localhost:27124"
         }
       }
     }
   }
   ```

   For pyenv users:
   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "/Users/username/.pyenv/versions/obsidian-mcp/bin/python",
         "args": ["-m", "src.server"],
         "cwd": "/Users/username/path/to/obsidian-mcp",
         "env": {
           "PYTHONPATH": "/Users/username/path/to/obsidian-mcp",
           "OBSIDIAN_REST_API_KEY": "your-api-key-here",
           "OBSIDIAN_API_URL": "https://localhost:27124"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop** (Cmd/Ctrl + R)

3. **Verify connection** - the Obsidian tools should appear in Claude's tool list

## Troubleshooting

### "Connection refused" error
- Ensure Obsidian is running
- Verify the Local REST API plugin is enabled
- Check that the port matches (default: 27124)
- Confirm the API key is correct

### "Certificate verify failed" error
- This is expected with the Local REST API's self-signed certificate
- The server handles this automatically

### "Module not found" error
- Ensure your virtual environment is activated
- Run from the project root: `python -m src.server`
- Verify PYTHONPATH includes the project directory

### Empty results when listing notes
- Specify a directory when using `list_notes` (e.g., "Daily", "Projects")
- Root directory listing requires recursive implementation
- Check if notes are in subdirectories

### Tags not updating
- Ensure notes have YAML frontmatter section
- Frontmatter must include a `tags:` field (even if empty)

## Security Considerations

- **Keep your API key secret** - never commit it to version control
- The server validates all paths to prevent directory traversal attacks
- All communication with Obsidian uses HTTPS (self-signed certificate)
- The server only accepts local connections through the REST API

## Development

### Code Style
- Uses FastMCP framework for MCP implementation
- Pydantic models for type safety and validation
- Modular architecture with separated concerns
- Comprehensive error handling and user-friendly messages

### Adding New Tools
1. Create tool function in appropriate module under `src/tools/`
2. Add Pydantic models if needed in `src/models/`
3. Register the tool in `src/server.py` with the `@mcp.tool()` decorator
4. Include comprehensive docstrings
5. Add tests in `tests/`
6. Test with MCP Inspector before deploying

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Write tests for new functionality
4. Ensure all tests pass
5. Commit your changes (`git commit -m 'Add amazing tool'`)
6. Push to the branch (`git push origin feature/amazing-tool`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [Anthropic](https://anthropic.com) for creating the Model Context Protocol
- [Obsidian](https://obsidian.md) team for the amazing note-taking app
- [coddingtonbear](https://github.com/coddingtonbear) for the Local REST API plugin
- [dsp-ant](https://github.com/dsp-ant) for the FastMCP framework