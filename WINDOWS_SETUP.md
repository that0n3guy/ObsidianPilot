# Windows Setup Guide for ObsidianPilot

## Quick Setup Steps

### 1. Install Dependencies
```cmd
cd C:\Users\jimmy\dev\obsidian-mcp
pip install -r requirements.txt
```

### 2. Install Your Enhanced Package
```cmd
# Install in development mode so changes are picked up
pip install -e .
```

### 3. Configure Claude Desktop

**Location**: `%APPDATA%\Claude\claude_desktop_config.json`
**Full Path**: `C:\Users\jimmy\AppData\Roaming\Claude\claude_desktop_config.json`

### Option A: Using Installed Package (Recommended)
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "obsidian-pilot",
      "env": {
        "OBSIDIAN_VAULT_PATH": "C:\\path\\to\\your\\obsidian\\vault"
      }
    }
  }
}
```

### Option B: Direct Python Execution
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "python",
      "args": ["-m", "obsidian_mcp.server"],
      "cwd": "C:\\Users\\jimmy\\dev\\obsidian-mcp",
      "env": {
        "PYTHONPATH": "C:\\Users\\jimmy\\dev\\obsidian-mcp",
        "OBSIDIAN_VAULT_PATH": "C:\\path\\to\\your\\obsidian\\vault"
      }
    }
  }
}
```

### Option C: Using uvx (if you have uv installed) UNTESTED
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["--from", "C:\\Users\\jimmy\\dev\\obsidian-mcp", "obsidian-pilot"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "C:\\path\\to\\your\\obsidian\\vault"
      }
    }
  }
}
```

## Important Notes

### Path Format
- Use **double backslashes** (`\\`) or **forward slashes** (`/`) in JSON
- Example: `"C:\\Users\\jimmy\\Documents\\MyVault"` or `"C:/Users/jimmy/Documents/MyVault"`

### Find Your Vault Path
Your Obsidian vault path might be something like:
- `C:\\Users\\jimmy\\Documents\\Obsidian Vault`
- `C:\\Users\\jimmy\\OneDrive\\Documents\\Notes`
- `D:\\MyNotes`

### Test Your Setup
1. Open Command Prompt in your project directory
2. Set environment variable: `set OBSIDIAN_VAULT_PATH=C:\path\to\your\vault`
3. Test run: `python -m obsidian_mcp.server`
4. Should see: "MCP server for direct filesystem access to Obsidian vaults"

## Your New Token-Efficient Tools

After setup, you'll have access to these new tools in Claude Desktop:

### `edit_note_section`
Edit specific sections without rewriting entire notes:
```
"Add a new task to my daily note under the Tasks section"
"Update the status section in my project note"
"Change the heading from 'Old Name' to 'New Name'"
```

### `edit_note_content`  
Replace specific text precisely:
```
"Change 'priority: low' to 'priority: high' in my note"
"Fix the typo 'recieve' to 'receive' throughout the document"
"Update the author name in the frontmatter"
```

## Troubleshooting

### "obsidian-mcp command not found"
Use Option B (Direct Python) instead.

### "Module not found" errors
Ensure you're in the project directory and ran `pip install -e .`

### "Vault not found" errors
Double-check your `OBSIDIAN_VAULT_PATH` points to the correct directory.

### Permission errors
Make sure Claude Desktop has permission to access your vault directory.

## Restart Claude Desktop
After changing the config file, restart Claude Desktop completely for changes to take effect.