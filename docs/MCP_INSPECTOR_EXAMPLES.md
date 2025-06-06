# MCP Inspector Test Examples

This document provides example parameters for testing each tool in the MCP Inspector.

## Setup

1. Run the MCP Inspector:
   ```bash
   npx @modelcontextprotocol/inspector -e OBSIDIAN_REST_API_KEY=$OBSIDIAN_REST_API_KEY python -m src.server
   ```

2. Open the Inspector UI at `http://localhost:5173`

3. Copy the parameters below into the Inspector to test each tool

## Tool Examples

### list_notes_tool
List all notes in the vault:
```json
{
  "recursive": true
}
```

List specific directory:
```json
{
  "directory": "Daily",
  "recursive": false
}
```

### create_note_tool
Create a new test note:
```json
{
  "path": "MCP-Test/inspector-test.md",
  "content": "# Test Note\n\nThis note was created using the MCP Inspector.\n\n## Features\n- Markdown formatting\n- Frontmatter support\n- Easy testing",
  "overwrite": false
}
```

### read_note_tool
Read an existing note:
```json
{
  "path": "README.md"
}
```

### update_note_tool
Update a note:
```json
{
  "path": "MCP-Test/test-update.md",
  "content": "# Updated Content\n\nThis note has been updated.",
  "create_if_not_exists": true
}
```

### delete_note_tool
Delete a note:
```json
{
  "path": "MCP-Test/delete-me.md"
}
```

### search_notes_tool
Search for notes:
```json
{
  "query": "test",
  "context_length": 100
}
```

### add_tags_tool
Add tags to a note:
```json
{
  "path": "MCP-Test/test-note.md",
  "tags": ["mcp-test", "inspector", "example"]
}
```

### remove_tags_tool
Remove tags from a note:
```json
{
  "path": "MCP-Test/test-note.md",
  "tags": ["example"]
}
```

### get_note_info_tool
Get metadata about a note:
```json
{
  "path": "README.md"
}
```

### move_note_tool
Move a note to a new location:
```json
{
  "source_path": "MCP-Test/old-name.md",
  "destination_path": "MCP-Test/Archive/new-name.md",
  "update_links": true
}
```

## Testing Tips

1. **Start with `list_notes_tool`** to see what's in your vault
2. **Create test notes in a `MCP-Test` folder** for easy cleanup
3. **Test error cases** by using non-existent paths
4. **Check Obsidian** after each operation to verify it worked
5. **Use the context_length parameter** in search to control result size

## Common Test Scenarios

### Create and Read Flow
1. Create a note with `create_note_tool`
2. Read it back with `read_note_tool`
3. Verify content matches

### Tag Management Flow
1. Create a note with content
2. Add tags with `add_tags_tool`
3. Get info with `get_note_info_tool` to verify tags
4. Remove some tags with `remove_tags_tool`

### Search and Update Flow
1. Search for existing notes with `search_notes_tool`
2. Pick a result and read it with `read_note_tool`
3. Update it with `update_note_tool`
4. Search again to verify changes