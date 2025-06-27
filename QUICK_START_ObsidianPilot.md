# ObsidianPilot Quick Start 🚁

## One-Command Installation

```bash
uvx ObsidianPilot
```

## Claude Desktop Configuration

Add this to your Claude Desktop config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["ObsidianPilot"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault"
      }
    }
  }
}
```

## What You Get

### 🎯 Token-Efficient Editing
- **Edit sections** without reading entire files
- **Replace specific text** with surgical precision
- **Preserve frontmatter** automatically

### ⚡ Blazing Fast Performance
- **5x faster searches** with SQLite indexing
- **90% less memory usage**
- **Offline operation** - no plugins needed

### 🛠️ Powerful Tools
- `edit_note_section` - 5 section editing operations
- `edit_note_content` - precise text replacement
- All original tools: search, create, update, delete, tags, links

## Example Usage

Ask Claude:
- *"Add a new task to the ## Tasks section in my daily note"*
- *"Update the status from 'In Progress' to 'Completed' in my project note"*
- *"Change the heading from '## Old Name' to '## New Name'"*
- *"Fix the typo 'recieve' to 'receive' throughout my notes"*

## Migration from obsidian-mcp

```bash
# Uninstall old version
pip uninstall obsidian-mcp

# Install ObsidianPilot
uvx ObsidianPilot

# Update Claude config command from "obsidian-mcp" to "ObsidianPilot"
```

**No breaking changes** - all your existing functionality continues to work!

---

**ObsidianPilot**: Your intelligent co-pilot for Obsidian vault management ✨