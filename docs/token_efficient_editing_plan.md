# Token-Efficient Editing Tools Implementation Plan

## Overview
Create two complementary tools for efficient note editing that handle frontmatter, section headings, and content updates without full file rewrites.

## ✅ Implementation Status: COMPLETE

The token-efficient editing tools have been successfully implemented and integrated into the Obsidian MCP server. Both tools are now available and fully functional.

### ✅ Implemented Tools

#### `edit_note_section` - Section-based editing
- **Status**: ✅ Complete and registered
- **Location**: `obsidian_mcp/tools/note_management.py:524`
- **Tool registration**: `obsidian_mcp/server.py:213`

#### `edit_note_content` - Precise text replacement  
- **Status**: ✅ Complete and registered
- **Location**: `obsidian_mcp/tools/note_management.py:707`
- **Tool registration**: `obsidian_mcp/server.py:279`

### ✅ Implementation Highlights

#### Token Efficiency Achieved
- **Section targeting**: Edit specific sections without reading entire file content into AI context
- **Precise replacements**: Replace exact text without needing full file in conversation
- **Frontmatter preservation**: Automatically detects and preserves YAML frontmatter
- **Streaming approach**: Read only necessary portions of files for operations

#### All Operations Implemented
1. **insert_after**: ✅ Add content immediately after section heading
2. **insert_before**: ✅ Add content immediately before section heading  
3. **replace_section**: ✅ Replace entire section including heading
4. **append_to_section**: ✅ Add content at end of section (before next heading)
5. **edit_heading**: ✅ Change just the heading text while preserving content

## Implementation Strategy

### 1. Two-Tool Approach

#### `edit_note_section` - For structured section-based edits
**Parameters:**
- `path`: Path to the note file
- `section_identifier`: Markdown heading to identify the section (e.g., "## Tasks", "### Status")
- `content`: Content to insert, replace, or append
- `operation`: Type of edit operation
- `create_if_missing`: Whether to create the section if it doesn't exist

**Operations:**
- `insert_after`: Add content immediately after the heading
- `insert_before`: Add content immediately before the heading
- `replace_section`: Replace entire section including heading
- `append_to_section`: Add content at the end of the section (before next heading)
- `edit_heading`: Change just the heading text while preserving section content

#### `edit_note_content` - For precise text replacement (like MCP filesystem)
**Parameters:**
- `path`: Path to the note file
- `search_text`: Exact text to search for
- `replacement_text`: Text to replace with
- `occurrence`: "first" or "all" occurrences

**Use cases:**
- Edit specific lines or values
- Update URLs or references
- Fix typos
- Modify frontmatter properties

### 2. Frontmatter Handling
- Detect frontmatter boundaries using `---` markers
- Special logic to skip frontmatter when searching for sections
- Preserve frontmatter formatting and structure
- For frontmatter edits, use `edit_note_content` with validation
- Handle edge cases: no frontmatter, malformed YAML, empty frontmatter

### 3. Efficient Implementation Details
- **Stream file content** instead of loading entire file into memory
- **Early termination**: Stop reading once target section/text is found
- **In-place writes** when possible to minimize disk I/O
- **Preserve formatting**: Maintain line endings, indentation, blank lines
- **Content buffering**: Only buffer necessary portions of the file

### 4. Section Detection Logic
- Use regex pattern for markdown headings: `^(#{1,6})\s+(.+)$`
- Case-insensitive matching for section identifiers
- Handle heading variations (with/without trailing #, spaces)
- Support hierarchical sections (detect section boundaries correctly)

### 5. Edge Cases to Handle
- **Multiple sections** with the same heading (use first match or add index parameter)
- **Nested sections** (## under #) - correctly determine section boundaries
- **Empty sections** - handle sections with no content
- **No trailing newline** - ensure file ends properly
- **Section at EOF** - handle sections at the end of file
- **Heading-only sections** - sections with just a heading and no content
- **Code blocks** - avoid matching headings inside code blocks

### 6. Error Handling
- Clear error messages for missing sections
- Validate markdown heading format
- Handle file not found gracefully
- Prevent invalid operations (e.g., insert_after on last line)
- Rollback on write failures

### 7. Testing Scenarios
- Edit section in middle of file
- Edit first/last section
- Create new section at specific location
- Edit heading without touching content
- Replace text across multiple lines
- Frontmatter preservation during section edits
- Large file performance (streaming works correctly)
- Unicode and special character handling

### 8. Performance Benefits
- **Token efficiency**: Only send changed content, not entire file
- **Reduced latency**: Faster operations on large files
- **Memory efficiency**: Stream processing instead of full file load
- **Precise updates**: Change only what's needed

### 9. Integration Points
- Add both tools to `note_management.py`
- Register in `server.py` with FastMCP decorators
- Update imports and __all__ exports
- Maintain consistent error handling with existing tools

### 10. Documentation Requirements
- Clear docstrings with examples for each operation
- Performance notes about when to use each tool
- Examples of common use cases
- Comparison with `update_note` for full replacements