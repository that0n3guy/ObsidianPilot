# Release Notes - v1.1.3

## Overview
This release brings significant improvements to folder and tag management, performance optimizations, and bug fixes that make the Obsidian MCP server more powerful and reliable.

## 🐛 Bug Fixes

### Fixed search_by_date for today's notes
- **Issue**: When searching for notes modified today (days_ago=0), the tool was using the current time instead of midnight, missing notes modified earlier in the day
- **Fix**: Now properly calculates from the start of the day (midnight)
- **Impact**: Users can now reliably find all notes modified today

### Fixed tag reading functionality
- **Issue**: Tags were not being properly read from notes, especially inline hashtags
- **Fix**: Added proper JSON format request headers and improved metadata parsing
- **Impact**: All tag-related tools now work correctly with both frontmatter tags and inline hashtags

## ✨ New Features

### Folder Management Tools

#### `list_folders`
- List all folders in your vault or a specific directory
- Supports recursive exploration of folder hierarchies
- Returns structured folder information with paths and names

#### `create_folder`
- Creates new folders including all parent folders in the path
- Example: "Apple/Studies/J71P" creates all three levels if needed
- Optionally creates placeholder files (.gitkeep or README.md)
- Reports which folders were created vs already existed

#### `move_folder`
- Move entire folders with all their contents
- Validates against circular references
- Reports detailed statistics (notes moved, folders created)
- Preserves note content during moves

### Enhanced Tag Management

#### `update_tags`
- New tool for AI-driven tag management
- Replace all tags or merge with existing ones
- Perfect for "analyze this note and suggest tags" workflows
- Returns both previous and new tag lists

#### `list_tags`
- Discover all unique tags used across your vault
- Optional usage statistics for each tag
- Sort by name or usage count
- Optimized with concurrent batching for large vaults

## ⚡ Performance Improvements

### Concurrent Operations
- Implemented asyncio.gather for parallel note fetching
- Batch processing (10 notes at a time) to avoid API overload
- Significantly faster performance for large vaults (>1000 notes)

### Optimized Tag Collection
- Uses search API to find tagged notes first
- Only fetches notes that actually have tags
- Reduces unnecessary API calls

## 📝 Documentation Improvements

### Enhanced Tool Documentation
- Added "When to use" and "When NOT to use" sections
- Included practical examples in Field annotations
- Improved error messages with actionable guidance

### MCP Best Practices Compliance
- Clear verb-object naming patterns
- Single, focused purpose for each tool
- Progressive disclosure with sensible defaults
- Predictable response patterns

## 🔧 Technical Improvements

### Better Error Handling
- Specific error messages for common issues
- Validation for all path operations
- Protection against directory traversal

### Code Organization
- Consistent patterns across all tools
- Improved type safety with Annotated types
- Better separation of concerns

## Breaking Changes
None - All changes are backward compatible.

## Migration Guide
No migration needed. The new tools are additive and don't affect existing functionality.

## What's Next
Future improvements could include:
- Link updating when moving notes/folders
- Bulk tag operations across multiple notes
- Advanced search with more filter options
- Template management tools

## Installation
```bash
# Using uvx (recommended)
uvx obsidian-mcp

# Or with pipx
pipx install obsidian-mcp

# Or with pip
pip install obsidian-mcp
```

## Credits
Thanks to all users who reported issues and suggested improvements!