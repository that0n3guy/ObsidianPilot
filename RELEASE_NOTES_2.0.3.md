# Release Notes - v2.0.3

## New Feature: Token-Efficient Section Editing

This release adds powerful new tools for editing notes efficiently without requiring full file content in AI conversations, significantly reducing token usage and improving performance.

### ✨ New Tools

#### `edit_note_section` - Surgical Section Editing
Edit specific markdown sections without rewriting entire notes:

- **insert_after**: Add content immediately after a section heading
- **insert_before**: Add content immediately before a section heading  
- **replace_section**: Replace an entire section including the heading
- **append_to_section**: Add content at the end of a section (before next heading)
- **edit_heading**: Change just the heading text while preserving section content

**Example usage:**
```python
# Add tasks to a specific section
edit_note_section("Daily/2024-01-15.md", "## Tasks", "- [ ] Review PR\n- [ ] Update docs", operation="append_to_section")

# Update a status section
edit_note_section("Projects/Website.md", "### Current Status", "### Current Status\n\nPhase 2 completed!", operation="replace_section")

# Change just a heading
edit_note_section("Projects/Website.md", "## Old Heading", "## New Heading", operation="edit_heading")
```

#### `edit_note_content` - Precise Text Replacement
Replace specific text without rewriting entire notes:

- Replace first occurrence or all occurrences
- Perfect for updating values, fixing typos, or modifying frontmatter
- Exact text matching for surgical precision

**Example usage:**
```python
# Update a specific value
edit_note_content("Projects/Website.md", "Status: In Progress", "Status: Completed")

# Fix typos throughout document
edit_note_content("Notes/Research.md", "recieve", "receive", occurrence="all")

# Update frontmatter properties
edit_note_content("Daily/2024-01-15.md", "priority: low", "priority: high")
```

### 🔧 Technical Implementation

#### Smart Frontmatter Handling
- Automatically detects and preserves YAML frontmatter during all operations
- Separates frontmatter from content to prevent corruption
- Maintains proper formatting and structure

#### Robust Section Detection
- Case-insensitive markdown heading matching
- Supports all heading levels (# through ######)
- Handles nested sections and complex document structures
- Optional section creation when sections don't exist

#### Token Efficiency Benefits
- **Reduced context size**: Edit specific sections without sending entire file content
- **Targeted operations**: Change only what needs to be changed
- **Preserved formatting**: Maintains document structure and whitespace
- **Streaming approach**: Processes only necessary file portions

### 🐛 Bug Fixes

#### FastMCP Compatibility
- Fixed deprecated import warnings for `fastmcp.Image`
- Updated to use `fastmcp.utilities.types.Image` following new FastMCP conventions
- Improved forward compatibility with future FastMCP versions

#### Import Issues
- Added missing `Tuple` and `Literal` type imports
- Fixed `NameError` issues that prevented server startup
- Ensured all dependencies are properly declared in requirements.txt

#### Dependencies
- Added missing dependencies: `aiofiles`, `aiosqlite`, `pyyaml`, `pillow`
- Updated requirements.txt with version constraints for better stability
- Fixed installation issues on Windows environments

### 📚 Documentation Updates

#### Windows Setup Guide
- Added comprehensive Windows setup instructions (`WINDOWS_SETUP.md`)
- Included multiple configuration options for different Python installations
- Added troubleshooting guides for common Windows issues
- Provided example configurations for Claude Desktop

#### Implementation Documentation
- Created detailed implementation plan (`docs/token_efficient_editing_plan.md`)
- Documented all edge cases and design decisions
- Added comprehensive test coverage examples

### 🧪 Testing

#### Comprehensive Test Suite
- Added full test coverage for section editing functionality (`tests/test_token_efficient_editing.py`)
- Tests for frontmatter preservation, section boundaries, and edge cases
- Temporary vault fixtures for isolated testing
- Coverage for all five section editing operations

### 🔄 Backward Compatibility

- **No breaking changes**: All existing tools and APIs remain unchanged
- **Additive enhancement**: New tools complement existing functionality
- **Configuration compatibility**: Existing Claude Desktop configurations continue to work
- **API consistency**: New tools follow the same patterns as existing tools

### 📊 Performance Impact

- **Memory efficient**: Tools only load necessary file portions
- **Faster operations**: Avoid processing entire files for small changes
- **Reduced bandwidth**: Smaller AI context requirements
- **Better scalability**: Handles large notes more efficiently

### 🚀 Use Cases

The new token-efficient editing tools are ideal for:

- **Daily note management**: Adding tasks, updating status sections
- **Project tracking**: Modifying project status, updating progress
- **Content organization**: Reorganizing sections, updating headings
- **Bulk corrections**: Fixing typos, updating references across notes
- **Metadata management**: Updating frontmatter properties
- **Incremental writing**: Building up notes section by section

### 🔧 Technical Requirements

- **Python**: 3.10 or higher (no change)
- **New dependencies**: aiofiles, aiosqlite, pyyaml, pillow
- **FastMCP**: 2.8.1 or higher (updated for compatibility)

This release represents a significant enhancement to the Obsidian MCP server, providing powerful new capabilities while maintaining full backward compatibility and following established patterns for seamless integration.