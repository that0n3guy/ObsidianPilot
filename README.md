# Obsidian MCP Server

A Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with your Obsidian vault. This server provides tools for reading, creating, searching, and managing notes in Obsidian through the Local REST API plugin.

## Features

- 📖 **Read notes** from your Obsidian vault
- ✍️ **Create and update notes** with automatic overwrite protection
- 🔍 **Search notes** using Obsidian's search functionality
- 📅 **Search by date** to find notes created or modified within specific time periods
- 📁 **List notes** recursively or by directory
- 🏷️ **Manage tags** in note frontmatter
- 📊 **Get note statistics** including word count and links
- 🔒 **Secure communication** with API key authentication
- 🧪 **Comprehensive testing** suite with unit, integration, and live tests

### Enhanced for AI Reasoning

This MCP server follows best practices for AI-friendly design:

- **🎯 Rich Parameter Validation**: All inputs are validated with clear constraints and helpful error messages
- **📋 JSON Schema Metadata**: Tools provide detailed schemas with examples, patterns, and limits
- **💬 Actionable Error Messages**: Errors explain what went wrong and how to fix it
- **📚 Comprehensive Documentation**: Each tool includes "when to use" and "when NOT to use" guidance
- **🔍 Smart Defaults**: Sensible defaults for optional parameters reduce complexity

## Prerequisites

- **Obsidian** with the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin installed and enabled
- **Python 3.10+** installed on your system
- **Node.js** (optional, for running MCP Inspector)

## Installation

### Quick Install

Run the Obsidian MCP server without cloning the repository:

```bash
uvx obsidian-mcp
```

#### Setup Instructions

1. **Install and configure Obsidian:**
   - Install the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin in Obsidian
   - Enable the plugin in Settings > Community plugins
   - Go to Settings > Local REST API
   - Copy your API key (you'll need this for step 2)

2. **Add to Claude Desktop:**
   
   Edit your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "uvx",
         "args": ["obsidian-mcp"],
         "env": {
           "OBSIDIAN_REST_API_KEY": "your-api-key-here"
         }
       }
     }
   }
   ```
   
   Replace `your-api-key-here` with the API key you copied from Obsidian.

3. **Restart Claude Desktop** to load the new configuration.

That's it! The server will now be available in Claude with access to your Obsidian vault.

### Development Installation

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

6. **Add to Claude Desktop (for development):**

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

## Project Structure

```
obsidian-mcp/
├── src/
│   ├── server.py           # Main entry point with rich parameter schemas
│   ├── tools/              # Tool implementations
│   │   ├── note_management.py    # CRUD operations
│   │   ├── search_discovery.py   # Search and navigation
│   │   └── organization.py       # Tags, moves, metadata
│   ├── models/             # Pydantic models for validation
│   │   └── obsidian.py    # Note, SearchResult, VaultItem models
│   ├── utils/              # Shared utilities
│   │   ├── obsidian_api.py      # REST API client wrapper
│   │   ├── validators.py        # Path validation, sanitization
│   │   └── validation.py        # Comprehensive parameter validation
│   └── constants.py       # API endpoints, defaults, enhanced error messages
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

⚠️ **IMPORTANT**: By default, this tool REPLACES the entire note content. Always read the note first if you need to preserve existing content.

**Parameters:**
- `path`: Path to the note to update
- `content`: New markdown content (REPLACES existing content unless using append)
- `create_if_not_exists` (default: `false`): Create if doesn't exist
- `merge_strategy` (default: `"replace"`): How to handle content
  - `"replace"`: Overwrites entire note content (default)
  - `"append"`: Adds new content to the end of existing content

**Safe Update Pattern:**
```python
# ALWAYS read first to preserve content
existing_note = await read_note("Daily/2024-01-15.md")
updated_content = existing_note["content"] + "\n\n## New Section\nAdded content"
await update_note("Daily/2024-01-15.md", updated_content)

# Or use append mode to add to the end
await update_note("Daily/2024-01-15.md", "## New Section\nAdded content", merge_strategy="append")
```

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

#### `search_by_date`
Search for notes by creation or modification date.

**Parameters:**
- `date_type` (default: `"modified"`): Either "created" or "modified"
- `days_ago` (default: `7`): Number of days to look back
- `operator` (default: `"within"`): Either "within" (last N days) or "exactly" (exactly N days ago)

**Returns:**
```json
{
  "query": "Notes modified within last 7 days",
  "count": 15,
  "results": [
    {
      "path": "Daily/2024-01-15.md",
      "date": "2024-01-15T10:30:00",
      "days_ago": 1
    }
  ]
}
```

**Example usage:**
- "Show me all notes modified this week" → `search_by_date("modified", 7, "within")`
- "Find notes created in the last 30 days" → `search_by_date("created", 30, "within")`
- "What notes were modified exactly 2 days ago?" → `search_by_date("modified", 2, "exactly")`

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

For development installations, see the [Development Installation](#development-installation) section above.

## Enhanced Error Handling

The server provides detailed, actionable error messages to help AI systems recover from errors:

### Example Error Messages

**Invalid Path**:
```
Invalid note path: '../../../etc/passwd'. 
Valid paths must: 1) End with .md or .markdown, 2) Use forward slashes (e.g., 'folder/note.md'), 
3) Not contain '..' or start with '/', 4) Not exceed 255 characters. 
Example: 'Daily/2024-01-15.md' or 'Projects/My Project.md'
```

**Empty Search Query**:
```
Search query cannot be empty. 
Valid queries: 1) Keywords: 'machine learning', 
2) Tags: 'tag:#project', 3) Paths: 'path:Daily/', 
4) Combined: 'tag:#urgent TODO'
```

**Invalid Date Parameters**:
```
Invalid date_type: 'invalid'. 
Must be either 'created' or 'modified'. 
Use 'created' to find notes by creation date, 'modified' for last edit date
```

## Troubleshooting

### "Connection refused" error
- Ensure Obsidian is running
- Verify the Local REST API plugin is enabled
- Check that the port matches (default: 27124)
- Confirm the API key is correct
- The enhanced error will show the exact URL and port being used

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

## Best Practices for AI Assistants

### Preventing Data Loss

1. **Always read before updating**: The `update_note` tool REPLACES content by default
2. **Use append mode for additions**: When adding to existing notes, use `merge_strategy="append"`
3. **Check note existence**: Use `read_note` to verify a note exists before modifying
4. **Be explicit about overwrites**: Only use `overwrite=true` when intentionally replacing content

### Recommended Workflows

**Safe note editing:**
1. Read the existing note first
2. Modify the content as needed
3. Update with the complete new content

**Adding to daily notes:**
- Use `merge_strategy="append"` to add entries without losing existing content

**Creating new notes:**
- Use `create_note` with `overwrite=false` (default) to prevent accidental overwrites

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

## Publishing (for maintainers)

To publish a new version to PyPI:

```bash
# Update version in pyproject.toml
# Build the package
python -m build

# Test locally
pip install dist/*.whl
obsidian-mcp --version

# Upload to TestPyPI first (optional)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

Users can then run with:
```bash
uvx obsidian-mcp
```

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