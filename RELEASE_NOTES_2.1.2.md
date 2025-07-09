# ObsidianPilot v2.1.2 Release Notes

## 🎯 Clarity Update: Improved Link Field Names & Better Defaults

### Overview
Version 2.1.2 improves the clarity of link-related tool responses by using more descriptive field names and making `check_validity=True` the default for `get_outgoing_links`. This helps AI assistants better understand the difference between how a link is written and where it actually resolves to, while providing the file paths needed in most use cases.

### 🔄 API Changes

#### Default Behavior Change
- `get_outgoing_links` now defaults to `check_validity=True`
- This means `file_path` and `exists` fields are included by default
- For performance-critical cases, you can still use `check_validity=False`

#### Enhanced read_note Tool
- Added `include_outgoing_links` parameter to get all links from the note
- Added `include_backlinks` parameter to get all notes linking to this note
- Both parameters default to `False` for backward compatibility
- When enabled, link data is included directly in the response, avoiding extra API calls

#### Field Name Updates
The following field names have been changed for clarity:

**In link objects (get_outgoing_links, find_broken_links):**
- `path` → `target`: The target path as written in the link (e.g., "my note" or "folder/my note")
- `actual_path` → `file_path`: The actual file path in the vault where the target resolves to
- `display_text`: Unchanged - the text shown to users (from aliases or markdown link text)

**In backlink objects (get_backlinks):**
- `link_text` → `display_text`: Consistent with outgoing links
- Added `target` field: Shows the actual link target that matched

#### Updated Response Format
```json
// Before (v2.1.1)
{
  "path": "my note.md",
  "display_text": "My Note",
  "type": "wiki",
  "exists": true,
  "actual_path": "subfolder/my note.md"  // Only when different
}

// After (v2.1.2)
{
  "target": "my note.md",              // The target path in the link
  "display_text": "My Note",           // What the user sees
  "type": "wiki",                      // Link type
  "exists": true,                      // Does it exist?
  "file_path": "subfolder/my note.md"     // Now included by default
}
```

### 🎯 Benefits
- **Clearer for AI**: AI assistants can now easily distinguish between the target path and where it resolves
- **Consistent**: `file_path` is now included by default (even if it's the same as `target`)
- **Practical defaults**: Since most use cases need the actual file paths, validity checking is now the default
- **Fewer API calls**: The enhanced `read_note` tool can fetch links in one call instead of three
- **Less confusion**: Clear distinction between `target` (what's in the link) and `display_text` (what users see)
- **Accurate terminology**: Matches Obsidian's wiki link syntax: `[[target|display_text]]`

### 📝 Migration Notes
This is a **breaking change** if you're parsing the link responses. Update your code to use:
- `target` instead of `path` for the target path in the link
- `file_path` instead of `actual_path` for the actual file location
- `display_text` remains unchanged

### Affected Tools
- `get_outgoing_links` - Now defaults to check_validity=True
- `get_backlinks` - Updated field names for consistency
- `find_broken_links` - Updated field names
- `check_links_validity_batch` (internal)

---

**Installation**: `pip install ObsidianPilot==2.1.2`