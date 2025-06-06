Here's a comprehensive README.md for your Obsidian MCP server project:

```markdown
# Obsidian MCP Server

A Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with your Obsidian vault. This server provides tools for reading, creating, searching, and managing notes in Obsidian through the Local REST API plugin.

## Features

- 📖 **Read notes** from your Obsidian vault
- ✍️ **Create and update notes** with automatic overwrite protection
- 🔍 **Search notes** using Obsidian's search functionality
- 📁 **List notes** recursively or by directory
- 🔒 **Secure communication** with API key authentication
- 🧪 **Easy testing** with MCP Inspector support

## Prerequisites

- **Obsidian** with the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin installed and enabled
- **Python 3.8+** installed on your system
- **Node.js** (for running MCP Inspector)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/natestrong/obsidian-mcp
   cd obsidian-mcp
   ```

2. **Create a virtual environment:**
   ```bash
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

5. **Configure environment variables:**
   ```bash
   export OBSIDIAN_REST_API_KEY="your-api-key-here"
   ```

   Or create a `.env` file:
   ```
   OBSIDIAN_REST_API_KEY=your-api-key-here
   ```

## Project Structure

```
obsidian-mcp/
├── src/
│   ├── __init__.py
│   └── server.py       # Main MCP server implementation
├── tests/
│   └── test_server.py  # Basic connection tests
├── docs/
│   ├── Build_Reasoning-Friendly_MCP_README.md
│   ├── FastMCP_README.md
│   └── obsidian_rest_api_README.md
├── requirements.txt    # Python dependencies
├── .gitignore
├── CLAUDE.md          # Instructions for Claude Code
└── README.md
```

## Available Tools

### Note Management

#### `read_note`
Read the content and metadata of a specific note.

**Parameters:**
- `path`: Path to the note (e.g., "Daily/2024-01-15.md")

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

#### `list_notes`
List notes in your vault with optional recursive traversal.

**Parameters:**
- `directory` (optional): Specific directory to list
- `recursive` (default: `true`): List all notes recursively

### Organization

#### `move_note`
Move a note to a new location.

**Parameters:**
- `source_path`: Current path of the note
- `destination_path`: New path for the note
- `update_links` (default: `true`): Update links in other notes

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
Get metadata about a note without retrieving its content.

**Parameters:**
- `path`: Path to the note

## Testing with MCP Inspector

1. **Ensure Obsidian is running** with the Local REST API plugin enabled

2. **Run the MCP Inspector:**
   ```bash
   npx @modelcontextprotocol/inspector -e OBSIDIAN_REST_API_KEY=$OBSIDIAN_REST_API_KEY python -m src.server
   ```

3. **Open the Inspector UI** at `http://localhost:5173` (or the URL shown in terminal)

4. **Test the tools:**
   - Click "List Tools" to see all available tools
   - Select a tool and fill in the parameters
   - Click "Execute" to test the tool
   - Check the response and verify in Obsidian

## Integration with Claude Desktop

1. **Add to Claude Desktop configuration:**

   Edit your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "python",
         "args": ["-m", "src.server"],
         "cwd": "/path/to/obsidian-mcp",
         "env": {
           "OBSIDIAN_REST_API_KEY": "your-api-key-here"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop** (Cmd/Ctrl + R)

3. **Verify connection** by checking the MCP tools icon in Claude's interface

## Troubleshooting

### "Connection refused" error
- Ensure Obsidian is running
- Verify the Local REST API plugin is enabled
- Check that the API key is correct

### "Certificate verify failed" error
- This is expected with the Local REST API's self-signed certificate
- The server handles this automatically with `verify=False`

### "Module not found" error
- Ensure your virtual environment is activated
- Run from the project root: `python -m src.server`
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Empty results when listing notes
- Check if your notes are in subdirectories (use `recursive=true`)
- Verify the REST API has access to your vault
- Try listing a specific directory first

## Security Considerations

- **Keep your API key secret** - never commit it to version control
- The server only accepts local connections through the REST API
- All communication with Obsidian is encrypted (though using a self-signed certificate)

## Development

### Running locally
```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python -m src.server
```

### Testing
```bash
# Run all tests (pytest optional)
python tests/run_tests.py

# Run specific test types
python tests/run_tests.py unit         # Unit tests (requires pytest)
python tests/run_tests.py integration  # Integration tests (requires pytest)  
python tests/run_tests.py live         # Live tests with real Obsidian

# Run live tests directly (no pytest needed)
python tests/test_live.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector -e OBSIDIAN_REST_API_KEY=$OBSIDIAN_REST_API_KEY python -m src.server
# See docs/MCP_INSPECTOR_EXAMPLES.md for test examples
```

### Adding new tools
1. Add the tool function to `src/server.py`
2. Use the `@mcp.tool()` decorator
3. Include comprehensive docstrings
4. Return consistent response formats
5. Test with MCP Inspector before deploying

### Documentation

Additional documentation is available in the `docs/` directory:
- **Build_Reasoning-Friendly_MCP_README.md** - Best practices for building MCP servers that work well with AI systems
- **FastMCP_README.md** - Technical guide for the FastMCP framework used in this project
- **obsidian_rest_api_README.md** - Complete reference for the Obsidian Local REST API

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Commit your changes (`git commit -m 'Add amazing tool'`)
4. Push to the branch (`git push origin feature/amazing-tool`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [Anthropic](https://anthropic.com) for creating the Model Context Protocol
- [Obsidian](https://obsidian.md) team for the amazing note-taking app
- [coddingtonbear](https://github.com/coddingtonbear) for the Local REST API plugin
```

This README provides a complete guide for users to understand, install, configure, and use your Obsidian MCP server. It includes practical examples, troubleshooting tips, and clear documentation of all the tools. You can customize it further based on your specific implementation details or additional features you plan to add.