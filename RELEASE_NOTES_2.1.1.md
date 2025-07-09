# ObsidianPilot v2.1.1 Release Notes

## 🐛 Bug Fix: Obsidian-Compatible Link Resolution

### Overview
Version 2.1.1 fixes a critical issue where the `get_outgoing_links` tool incorrectly resolved internal links, returning paths in the root folder when the actual files were in subfolders. This update implements Obsidian's proper link resolution algorithm.

### 🎯 Issue Fixed
- **❌ Incorrect Link Paths**: Links like `[[here is a test file]]` were always resolved to the root folder
- **✅ Now Fixed**: Links are properly resolved relative to the source note's directory first, matching Obsidian's behavior

### 🔧 Technical Details

#### Link Resolution Algorithm
The fix implements Obsidian's link resolution order:
1. **Relative Resolution**: First checks for the file relative to the current note's directory
2. **Exact Path Match**: Then checks if the link is already a full path
3. **Shortest Path**: Finally searches for the shortest path to a file with that name

#### Updated Functions
- `extract_links_from_content()`: Now accepts `source_path` parameter for context
- `find_notes_by_names()`: Implements proper Obsidian link resolution algorithm
- `check_links_validity_batch()`: Passes source path for relative resolution
- `get_outgoing_links()`: Provides source note path for link resolution
- `find_broken_links()`: Updates each note's links with proper relative context

### Example
For a note at `subfolder/my-note.md` containing `[[test file]]`:
- **Before**: Always returned `test file.md` (root folder)
- **After**: First checks `subfolder/test file.md`, then falls back to other locations

### Backward Compatibility
This is a bug fix with no breaking changes. All existing functionality remains the same, but link resolution is now accurate.

---

**Installation**: `pip install ObsidianPilot==2.1.1`