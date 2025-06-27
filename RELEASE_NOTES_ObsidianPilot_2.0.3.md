# Release Notes - ObsidianPilot v2.0.3

## 🚀 Introducing ObsidianPilot!

This release rebrands the enhanced Obsidian MCP server as **ObsidianPilot** - your intelligent co-pilot for Obsidian vault management with powerful token-efficient editing capabilities.

### ✨ New Brand, Enhanced Features

#### Package Rebrand
- **New name**: `ObsidianPilot` (was `obsidian-mcp`)
- **New command**: `obsidian-pilot` (or `uvx ObsidianPilot`)
- **Same powerful features** with a distinctive identity

#### Installation & Usage
```bash
# Simple installation with uvx
uvx ObsidianPilot

# Or install with pipx
pipx install ObsidianPilot

# Claude Desktop config
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["ObsidianPilot"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
```

### 🎯 Token-Efficient Editing Features

#### `edit_note_section` - Surgical Section Editing
Edit specific markdown sections without rewriting entire notes:

- **insert_after**: Add content immediately after a section heading
- **insert_before**: Add content immediately before a section heading  
- **replace_section**: Replace an entire section including the heading
- **append_to_section**: Add content at the end of a section (before next heading)
- **edit_heading**: Change just the heading text while preserving section content

#### `edit_note_content` - Precise Text Replacement
Replace specific text without rewriting entire notes:
- Replace first occurrence or all occurrences
- Perfect for updating values, fixing typos, or modifying frontmatter
- Exact text matching for surgical precision

### 🛡️ Advanced Features

#### Smart Frontmatter Handling
- Automatically detects and preserves YAML frontmatter during all operations
- Separates frontmatter from content to prevent corruption
- Maintains proper formatting and structure

#### Robust Section Detection
- Case-insensitive markdown heading matching
- Supports all heading levels (# through ######)
- Handles nested sections and complex document structures
- Optional section creation when sections don't exist

### 🚀 Performance Benefits

#### Token Efficiency
- **Reduced context size**: Edit specific sections without sending entire file content
- **Targeted operations**: Change only what needs to be changed
- **Preserved formatting**: Maintains document structure and whitespace
- **Streaming approach**: Processes only necessary file portions

#### Speed & Memory
- **5x faster searches** with persistent SQLite indexing
- **90% less memory usage** compared to traditional approaches
- **Offline operation** - no plugins required
- **Concurrent operations** for large vaults

### 🐛 Bug Fixes & Improvements

#### FastMCP Compatibility
- Fixed deprecated import warnings for `fastmcp.Image`
- Updated to use `fastmcp.utilities.types.Image` following new FastMCP conventions
- Improved forward compatibility with future FastMCP versions

#### Dependencies & Installation
- Added missing dependencies: `aiofiles`, `aiosqlite`, `pyyaml`, `pillow`
- Updated requirements.txt with version constraints for better stability
- Fixed installation issues on Windows environments
- Added missing `Tuple` and `Literal` type imports

### 📚 Documentation & Setup

#### Comprehensive Guides
- **Windows Setup Guide**: Step-by-step installation instructions
- **Publishing Guide**: How to contribute and extend ObsidianPilot
- **Implementation Documentation**: Detailed technical documentation
- **Example Configurations**: Ready-to-use Claude Desktop configs

#### Enhanced Tool Documentation
- Updated all tool descriptions with accurate operation names
- Added comprehensive examples for each editing operation
- Documented token efficiency benefits and use cases

### 🎯 Use Cases

ObsidianPilot excels at:

- **Daily note management**: Adding tasks, updating status sections
- **Project tracking**: Modifying project status, updating progress  
- **Content organization**: Reorganizing sections, updating headings
- **Bulk corrections**: Fixing typos, updating references across notes
- **Metadata management**: Updating frontmatter properties
- **Incremental writing**: Building up notes section by section

### 🔄 Migration Guide

#### From Previous Versions
If you were using the previous `obsidian-mcp` package:

1. **Uninstall old version**:
   ```bash
   pip uninstall obsidian-mcp
   ```

2. **Install ObsidianPilot**:
   ```bash
   uvx ObsidianPilot
   ```

3. **Update Claude Desktop config**:
   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "uvx",
         "args": ["ObsidianPilot"],
         "env": {
           "OBSIDIAN_VAULT_PATH": "/path/to/your/vault"
         }
       }
     }
   }
   ```

#### No Breaking Changes
- All existing functionality remains unchanged
- Same API and tool interfaces
- Configuration format stays the same (just update command)

### 🛠️ Technical Requirements

- **Python**: 3.10 or higher
- **Dependencies**: FastMCP 2.8.1+, aiofiles, aiosqlite, pyyaml, pillow
- **Storage**: Persistent SQLite index in `.obsidian/mcp-search-index.db`

### 🎉 What's Next

ObsidianPilot represents a significant enhancement to Obsidian-AI integration:

- **Community-driven development** with active maintenance
- **Token-efficient design** reducing AI interaction costs
- **Windows-first compatibility** with comprehensive setup guides
- **Extensible architecture** ready for community contributions

Experience the future of intelligent Obsidian vault management with ObsidianPilot! 🚁✨