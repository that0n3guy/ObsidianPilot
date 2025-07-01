## ObsidianPilot - Enhanced MCP Server

## 🚀 Quick Start (Windows)

1. **Setup Claude Desktop:**
Visit this page for details: https://modelcontextprotocol.io/quickstart/user

2. **Configure Claude Desktop:**
   - Open: `%APPDATA%\Claude\claude_desktop_config.json`
   - Add this configuration:
   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "obsidianpilot",
         "args": [],
         "env": {
           "OBSIDIAN_VAULT_PATH": "C:\\Users\\YourName\\Documents\\MyVault"
         }
       }
     }
   }
   ```

3. **Update the vault path in the config above** to your actual Obsidian vault location

4. **Restart Claude Desktop** - You must click file->exit... not just close and reopen.   Then ObsidianPilot is now ready!

---

### 🎉 Version 2.1.0 Released!

**🚀 Revolutionary Search Performance Update:**

-   ⚡ **100-1000x faster search** - SQLite FTS5 full-text search replaces slow SQL LIKE queries
-   🔍 **Boolean search operators** - Use AND, OR, NOT for complex queries like `"Eide Bailly OR CPA OR accounting"`
-   🚫 **No more timeouts** - Search tools that hung indefinitely on large vaults (1800+ notes) now complete in <0.5 seconds
-   🤖 **Smart auto-optimization** - Tools automatically detect vault size and choose fastest search method
-   🗂️ **Field-specific search** - Target filename, tags, properties, or content with optimized indexes
-   🔄 **Background indexing** - Index builds automatically without blocking AI interactions
-   📊 **Search analytics** - Monitor index status and performance with built-in stats
-   🎯 **Intelligent fallbacks** - Seamless compatibility with legacy search tools

**Previous v2.0 features:**
-   🖼️ **Image support** - View and analyze images from your vault
-   🔍 **Powerful regex search** - Find complex patterns in your notes  
-   🚀 **Simple setup** - Quick Windows configuration guide included
-   🔄 **Direct filesystem access** - No plugins required, works offline
-   📦 **Token-efficient editing** - Edit specific sections without rewriting entire notes

* * *

ObsidianPilot is an enhanced Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with your Obsidian vault with powerful token-efficient editing capabilities. This server provides tools for reading, creating, searching, and managing notes in Obsidian through direct filesystem access with blazing-fast performance and intelligent indexing.

### Features

-   📖 **Read & write notes** - Full access to your Obsidian vault with automatic overwrite protection
-   🔍 **Blazing-fast search** - SQLite FTS5 full-text search with boolean operators (AND, OR, NOT) for instant results on large vaults
-   ⚡ **Smart search optimization** - Automatically chooses fastest search method based on vault size and query complexity
-   🖼️ **Image analysis** - View and analyze images embedded in notes or stored in your vault
-   🔎 **Regex power search** - Use regular expressions to find code patterns, URLs, or complex text structures
-   🗂️ **Property search** - Query notes by frontmatter properties with operators (=, >, <, contains, exists)
-   📁 **Browse vault** - List and navigate your notes and folders by directory
-   🏷️ **Tag management** - Add, remove, and organize tags (supports hierarchical tags, frontmatter, and inline tags)
-   🔗 **Link management** - Find backlinks, analyze outgoing links, and identify broken links
-   ✏️ **Smart rename** - Rename notes with automatic link updates throughout your vault
-   📊 **Note insights** - Get statistics like word count and link analysis
-   🎯 **AI-optimized** - Clear error messages and smart defaults for better AI interactions
-   🔒 **Secure** - Direct filesystem access with path validation
-   ⚡ **Performance optimized** - Persistent SQLite index, concurrent operations, and streaming for large vaults
-   🚀 **Bulk operations** - Create folder hierarchies and move entire folders with all their contents

### Prerequisites

-   **Obsidian** vault on your local filesystem
-   **Python 3.10+** installed on your system
-   **Node.js** (optional, for running MCP Inspector)

### Installation

#### For Other Platforms (macOS, Linux)

**Install ObsidianPilot:**
```bash
uvx ObsidianPilot
```

#### Configuration for All Platforms

1.  **Locate your Obsidian vault:**
    -   Find the path to your Obsidian vault on your filesystem
    -   Example: `/Users/yourname/Documents/MyVault` or `C:\Users\YourName\Documents\MyVault`
2.  **Configure your AI tool:**Edit your Claude Desktop config file:
    
    -   macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
    -   Windows: `%APPDATA%\Claude\claude_desktop_config.json`
    
    { "mcpServers": { "obsidian": { "command": "uvx", "args": \["ObsidianPilot"\], "env": { "OBSIDIAN\_VAULT\_PATH": "/path/to/your/obsidian/vault" } } } }
    
    Add to your Cursor settings:
    
    -   Project-specific: `.cursor/mcp.json` in your project directory
    -   Global: `~/.cursor/mcp.json` in your home directory
    
    { "mcpServers": { "obsidian": { "command": "uvx", "args": \["ObsidianPilot"\], "env": { "OBSIDIAN\_VAULT\_PATH": "/path/to/your/obsidian/vault" } } } }
    
    Then: Open Settings → Cursor Settings → Enable MCP
    
    Edit your Windsurf config file:
    
    -   Location: `~/.codeium/windsurf/mcp_config.json`
    
    { "mcpServers": { "obsidian": { "command": "uvx", "args": \["ObsidianPilot"\], "env": { "OBSIDIAN\_VAULT\_PATH": "/path/to/your/obsidian/vault" } } } }
    
    Then: Open Windsurf Settings → Advanced Settings → Cascade → Add Server → Refresh
    
3.  **Restart your AI tool** to load the new configuration.

That's it! The server will now be available in your AI tool with access to your Obsidian vault.

> **Note:** This uses `uvx` which automatically downloads and runs the server in an isolated environment. Most users won't need to install anything else. If you don't have `uv` installed, you can also use `pipx install ObsidianPilot` and change the command to `"obsidianpilot"` in the config.

##### Try It Out

Here are some example prompts to get started:

-   "Show me all notes I modified this week"
-   "Create a new daily note for today with my meeting agenda"
-   "Search for all notes about project planning"
-   "Read my Ideas/startup.md note"

#### Development Installation

1.  **Clone the repository:**
    
    git clone https://github.com/that0n3guy/ObsidianPilot cd ObsidianPilot
    
2.  **Set up Python environment:**
    
    \# Using pyenv (recommended) pyenv virtualenv 3.12.9 ObsidianPilot pyenv activate ObsidianPilot \# Or using venv python -m venv venv source venv/bin/activate \# On Windows: venv\\Scripts\\activate
    
3.  **Install dependencies:**
    
    pip install -r requirements.txt
    
4.  **Configure environment variables:**
    
    export OBSIDIAN\_VAULT\_PATH="/path/to/your/obsidian/vault"
    
5.  **Run the server:**
    
    python -m obsidian\_mcp.server
    
6.  **Add to Claude Desktop (for development):**Edit your Claude Desktop config file:
    
    -   macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
    -   Windows: `%APPDATA%\Claude\claude_desktop_config.json`
    
    { "mcpServers": { "obsidian": { "command": "/path/to/python", "args": \["\-m", "obsidian\_mcp.server"\], "cwd": "/path/to/ObsidianPilot", "env": { "PYTHONPATH": "/path/to/ObsidianPilot", "OBSIDIAN\_VAULT\_PATH": "/path/to/your/obsidian/vault" } } } }
    

### Project Structure

obsidian\-mcp/ ├── obsidian\_mcp/ │ ├── server.py # Main entry point with rich parameter schemas │ ├── tools/ # Tool implementations │ │ ├── note\_management.py # CRUD operations │ │ ├── search\_discovery.py # Search and navigation │ │ ├── organization.py # Tags, moves, metadata │ │ └── link\_management.py # Backlinks, outgoing links, broken links │ ├── models/ # Pydantic models for validation │ │ └── obsidian.py # Note, SearchResult, VaultItem models │ ├── utils/ # Shared utilities │ │ ├── filesystem.py # Direct filesystem access │ │ ├── validators.py # Path validation, sanitization │ │ └── validation.py # Comprehensive parameter validation │ └── constants.py # Constants and error messages ├── tests/ │ ├── run\_tests.py # Test runner │ └── test\_filesystem\_integration.py # Integration tests ├── docs/ # Additional documentation ├── requirements.txt # Python dependencies ├── CLAUDE.md # Instructions for Claude Code └── README.md

### Available Tools

#### Note Management

##### `read_note`

Read the content and metadata of a specific note.

**Parameters:**

-   `path`: Path to the note (e.g., "Daily/2024-01-15.md")

**Returns:**

{ "path": "Daily/2024-01-15.md", "content": "\# Daily Note\\n\\nContent here...", "metadata": { "tags": \["daily", "journal"\], "aliases": \[\], "frontmatter": {} } }

##### `create_note`

Create a new note or update an existing one.

**Parameters:**

-   `path`: Path where the note should be created
-   `content`: Markdown content of the note (consider adding tags for organization)
-   `overwrite` (default: `false`): Whether to overwrite existing notes

**Best Practices:**

-   Add relevant tags when creating notes to maintain organization
-   Use `list_tags` to see existing tags and maintain consistency
-   Tags can be added as inline hashtags (`#tag`) or in frontmatter

##### `update_note`

Update the content of an existing note.

⚠️ **IMPORTANT**: By default, this tool REPLACES the entire note content. Always read the note first if you need to preserve existing content.

**Parameters:**

-   `path`: Path to the note to update
-   `content`: New markdown content (REPLACES existing content unless using append)
-   `create_if_not_exists` (default: `false`): Create if doesn't exist
-   `merge_strategy` (default: `"replace"`): How to handle content
    -   `"replace"`: Overwrites entire note content (default)
    -   `"append"`: Adds new content to the end of existing content

**Safe Update Pattern:**

1.  ALWAYS read first to preserve content
2.  Modify the content as needed
3.  Update with the complete new content
4.  Or use append mode to add content to the end

##### `edit_note_section`

Edit a specific section of a note identified by a markdown heading.

**Parameters:**

-   `path`: Path to the note to edit
-   `section_identifier`: Markdown heading that identifies the section (e.g., "## Tasks", "### Status")
-   `content`: Content to insert, replace, or append
-   `operation` (default: `"insert_after"`): How to edit the section
    -   `"insert_after"`: Add content after the section heading
    -   `"insert_before"`: Add content before the section heading
    -   `"replace_section"`: Replace entire section including heading
    -   `"append_to_section"`: Add content at the end of the section
    -   `"edit_heading"`: Change just the heading text while preserving section content
-   `create_if_missing` (default: `false`): Create section if it doesn't exist

**Example usage:**

# Add tasks to a specific section
await edit_note_section(
    "Daily/2024-01-15.md",
    "## Tasks", 
    "- [ ] Review PR\n- [ ] Update docs",
    operation="append_to_section"
)

# Update a status section
await edit_note_section(
    "Projects/Website.md",
    "### Current Status",
    "### Current Status\n\nPhase 2 completed!",
    operation="replace_section"
)

# Change just a heading
await edit_note_section(
    "Projects/Website.md", 
    "## Old Heading",
    "## New Heading",
    operation="edit_heading"
)

**Use cases:**

-   Adding items to task lists without rewriting the whole note
-   Updating status sections in project notes
-   Building up notes incrementally by section
-   Inserting content at precise locations

##### `edit_note_content`

Edit specific text content in a note using precise search and replace.

**Parameters:**

-   `path`: Path to the note to edit
-   `search_text`: Exact text to search for and replace
-   `replacement_text`: Text to replace the search_text with
-   `occurrence` (default: `"first"`): Replace "first" occurrence only or "all" occurrences

**Example usage:**

# Update a specific value
await edit_note_content(
    "Projects/Website.md",
    "Status: In Progress",
    "Status: Completed"
)

# Fix a typo throughout the document
await edit_note_content(
    "Notes/Research.md",
    "recieve",
    "receive",
    occurrence="all"
)

# Update frontmatter property
await edit_note_content(
    "Daily/2024-01-15.md",
    "priority: low",
    "priority: high"
)

**Use cases:**

-   Updating specific values or references
-   Fixing typos or correcting text
-   Modifying frontmatter properties
-   Changing URLs or links
-   Updating dates or numbers

##### `delete_note`

Delete a note from the vault.

**Parameters:**

-   `path`: Path to the note to delete

#### Search and Discovery

> **🚀 Performance Note:** v2.1.0 introduces blazing-fast SQLite FTS5 search that automatically optimizes for large vaults. Search tools that previously timed out on 1800+ note vaults now complete in under 0.5 seconds!

##### `search_notes` (Ultra-Fast FTS5 Search)

Lightning-fast full-text search using SQLite FTS5 indexing with boolean operators and advanced search capabilities.

**Performance Features:**
- **100-1000x faster**: SQLite FTS5 indexing replaces slow SQL LIKE queries
- **Boolean operators**: Support for AND, OR, NOT for complex searches
- **Phrase search**: Automatic phrase detection for multi-word queries
- **Proper ranking**: Results ranked by relevance with scoring
- **Background indexing**: Index builds automatically without blocking AI interactions
- **Legacy compatibility**: Supports tag:, path:, and property: prefixes for backward compatibility

**Parameters:**

-   `query`: Search query with boolean operators and special prefixes
-   `max_results` (default: `50`): Maximum number of results to return (1-500)
-   `context_length` (default: `100`): Number of characters to show around matches

**Search Syntax:**

**Boolean Search (New):**
-   `"python AND tutorial"` - Find notes containing both terms
-   `"Eide Bailly OR CPA OR accounting"` - Find notes with any of these terms
-   `"machine learning NOT snake"` - Exclude irrelevant results
-   `"(python OR ruby) AND tutorial"` - Complex nested queries
-   `"exact phrase search"` - Phrase matching for multi-word terms

**Legacy Syntax (Still Supported):**
-   Text search: `"machine learning"`
-   Tag search: `tag:project` or `tag:#project`
    -   Hierarchical tags: `tag:project/web` (exact match)
    -   Parent search: `tag:project` (finds project, project/web, project/mobile)
    -   Child search: `tag:web` (finds project/web, design/web)
-   Path search: `path:Daily/`
-   Property search: `property:status:active` or `property:priority:>2`

**Returns:**

{ "results": \[...\], // Array of matched notes "total\_count": 150, // Total matches found "limit": 50, // max\_results used "truncated": true // More results available }

**Property Search Examples:**

-   `property:status:active` - Find notes where status = "active"
-   `property:priority:>2` - Find notes where priority > 2
-   `property:author:*john*` - Find notes where author contains "john"
-   `property:deadline:*` - Find notes that have a deadline property
-   `property:rating:>=4` - Find notes where rating >= 4
-   `property:tags:project` - Find notes with "project" in their tags array
-   `property:due_date:<2024-12-31` - Find notes with due dates before Dec 31, 2024

##### `search_by_date`

Search for notes by creation or modification date.

**Parameters:**

-   `date_type` (default: `"modified"`): Either "created" or "modified"
-   `days_ago` (default: `7`): Number of days to look back
-   `operator` (default: `"within"`): Either "within" (last N days) or "exactly" (exactly N days ago)

**Returns:**

{ "query": "Notes modified within last 7 days", "count": 15, "results": \[ { "path": "Daily/2024-01-15.md", "date": "2024-01-15T10:30:00", "days\_ago": 1 } \] }

**Example usage:**

-   "Show me all notes modified today" → `search_by_date("modified", 0, "within")`
-   "Show me all notes modified this week" → `search_by_date("modified", 7, "within")`
-   "Find notes created in the last 30 days" → `search_by_date("created", 30, "within")`
-   "What notes were modified exactly 2 days ago?" → `search_by_date("modified", 2, "exactly")`

##### `search_by_regex` (Performance Optimized)

Search for notes using regular expressions with smart timeout protection for large vaults.

**v2.1.0 Improvements:**
- **Timeout protection**: 20-30s timeouts prevent hanging on large vaults
- **Smart suggestions**: Detects simple patterns and suggests faster alternatives
- **Auto-optimization**: Reduces result limits and applies timeouts based on vault size
- **Helpful errors**: When timeouts occur, suggests specific fast search alternatives

**Parameters:**

-   `pattern`: Regular expression pattern to search for
-   `flags` (optional): List of regex flags ("ignorecase", "multiline", "dotall")
-   `context_length` (default: `100`): Characters to show around matches
-   `max_results` (default: `50`): Maximum number of results (auto-limited for large vaults)

**Performance Tips:**
For better performance on large vaults, consider these alternatives:
- Simple text: Use `search_notes("your text")` 
- Boolean queries: Use `search_notes("term1 AND term2")`
- Field search: Use `search_notes("tag:tagname")` or `search_notes("path:foldername")`

**When to use regex:**
-   Finding code patterns (functions, imports, syntax)
-   Searching for structured data
-   Complex text patterns that simple search can't handle

**Common patterns:**

\# Find Python imports "(import|from)\\\\s+fastmcp" \# Find function definitions "def\\\\s+\\\\w+\\\\s\*\\\\(\[^)\]\*\\\\):" \# Find TODO comments "(TODO|FIXME)\\\\s\*:?\\\\s\*(.+)" \# Find URLs "https?://\[^\\\\s)>\]+" \# Find code blocks "\`\`\`python(\[^\`\]+)\`\`\`"

**Returns:**

{ "pattern": "def\\\\s+search\\\\w\*", "count": 2, "results": \[ { "path": "code/utils.py", "match\_count": 3, "matches": \[ { "match": "def search\_notes", "line": 42, "context": "...async def search\_notes(query)..." } \] } \] }

##### `search_by_property`

Search for notes by their frontmatter property values with advanced filtering.

**Parameters:**

-   `property_name`: Name of the property to search for
-   `value` (optional): Value to compare against
-   `operator` (default: `"="`): Comparison operator
-   `context_length` (default: `100`): Characters of note content to include

**Operators:**

-   `"="`: Exact match (case-insensitive)
-   `"!="`: Not equal
-   `">"`, `"<"`, `">="`, `"<="`: Numeric/date comparisons
-   `"contains"`: Property value contains the search value
-   `"exists"`: Property exists (value parameter ignored)

**Supported Property Types:**

-   **Text/String**: Standard text comparison
-   **Numbers**: Automatic numeric comparison for operators
-   **Dates**: ISO format (YYYY-MM-DD) with intelligent date parsing
-   **Arrays/Lists**: Searches within array items, comparisons use array length
-   **Legacy properties**: Automatically handles `tag`→`tags`, `alias`→`aliases` migrations

**Returns:**

{ "property": "status", "operator": "\=", "value": "active", "count": 5, "results": \[ { "path": "Projects/Website.md", "matches": \["status = active"\], "context": "status: active\\n\\n\# Website Redesign Project...", "property\_value": "active" } \] }

**Example usage:**

-   Find all active projects: `search_by_property("status", "active")`
-   Find high priority items: `search_by_property("priority", "2", ">")`
-   Find notes with deadlines: `search_by_property("deadline", operator="exists")`
-   Find notes by partial author: `search_by_property("author", "john", "contains")`

##### `list_notes`

List notes in your vault with optional recursive traversal.

**Parameters:**

-   `directory` (optional): Specific directory to list (e.g., "Daily", "Projects")
-   `recursive` (default: `true`): List all notes recursively

**Returns:**

{ "directory": "Daily", "recursive": true, "count": 365, "notes": \[ {"path": "Daily/2024-01-01.md", "name": "2024-01-01.md"}, {"path": "Daily/2024-01-02.md", "name": "2024-01-02.md"} \] }

##### `list_folders`

List folders in your vault with optional recursive traversal.

**Parameters:**

-   `directory` (optional): Specific directory to list from
-   `recursive` (default: `true`): Include all nested subfolders

**Returns:**

{ "directory": "Projects", "recursive": true, "count": 12, "folders": \[ {"path": "Projects/Active", "name": "Active"}, {"path": "Projects/Archive", "name": "Archive"}, {"path": "Projects/Ideas", "name": "Ideas"} \] }

#### Organization

##### `create_folder`

Create a new folder in the vault, including all parent folders in the path.

**Parameters:**

-   `folder_path`: Path of the folder to create (e.g., "Research/Studies/2024")
-   `create_placeholder` (default: `true`): Whether to create a placeholder file

**Returns:**

{ "folder": "Research/Studies/2024", "created": true, "placeholder\_file": "Research/Studies/2024/.gitkeep", "folders\_created": \["Research", "Research/Studies", "Research/Studies/2024"\] }

**Note:** This tool will create all necessary parent folders. For example, if "Research" exists but "Studies" doesn't, it will create both "Studies" and "2024".

##### `move_note`

Move a note to a new location, optionally with a new name.

**Parameters:**

-   `source_path`: Current path of the note
-   `destination_path`: New path for the note (can include new filename)
-   `update_links` (default: `true`): Update links if filename changes

**Features:**

-   Can move to a different folder: `move_note("Inbox/Note.md", "Archive/Note.md")`
-   Can move AND rename: `move_note("Inbox/Old.md", "Archive/New.md")`
-   Automatically detects if filename changes and updates all wiki-style links
-   No link updates needed for simple folder moves (Obsidian links work by name)
-   Preserves link aliases when updating

**Returns:**

{ "success": true, "source": "Inbox/Quick Note.md", "destination": "Projects/Project Plan.md", "renamed": true, "details": { "links\_updated": 5, "notes\_updated": 3 } }

##### `rename_note`

Rename a note and automatically update all references to it throughout your vault.

**Parameters:**

-   `old_path`: Current path of the note
-   `new_path`: New path for the note (must be in same directory)
-   `update_links` (default: `true`): Automatically update all wiki-style links

**Returns:**

{ "success": true, "old\_path": "Projects/Old Name.md", "new\_path": "Projects/New Name.md", "operation": "renamed", "details": { "links\_updated": 12, "notes\_updated": 8, "link\_update\_details": \[ {"note": "Daily/2024-01-15.md", "updates": 2}, {"note": "Ideas/Related.md", "updates": 1} \] } }

**Features:**

-   Automatically finds and updates all `[[wiki-style links]]` to the renamed note
-   Preserves link aliases (e.g., `[[Old Name|Display Text]]` → `[[New Name|Display Text]]`)
-   Handles various link formats: `[[Note]]`, `[[Note.md]]`, `[[Note|Alias]]`
-   Shows which notes were updated for transparency
-   Can only rename within the same directory (use `move_note` to change directories)

##### `move_folder`

Move an entire folder and all its contents to a new location.

**Parameters:**

-   `source_folder`: Current folder path (e.g., "Projects/Old")
-   `destination_folder`: New folder path (e.g., "Archive/Projects/Old")
-   `update_links` (default: `true`): Update links in other notes (future enhancement)

**Returns:**

{ "source": "Projects/Completed", "destination": "Archive/2024/Projects", "moved": true, "notes\_moved": 15, "folders\_moved": 3, "links\_updated": 0 }

##### `add_tags`

Add tags to a note's frontmatter.

**Parameters:**

-   `path`: Path to the note
-   `tags`: List of tags to add (without # prefix)

**Supports hierarchical tags:**

-   Simple tags: `["project", "urgent"]`
-   Hierarchical tags: `["project/web", "work/meetings/standup"]`
-   Mixed: `["urgent", "project/mobile", "status/active"]`

##### `update_tags`

Update tags on a note - either replace all tags or merge with existing.

**Parameters:**

-   `path`: Path to the note
-   `tags`: New tags to set (without # prefix)
-   `merge` (default: `false`): If true, adds to existing tags. If false, replaces all tags

**Perfect for AI workflows:**

User: "Tell me what this note is about and add appropriate tags" AI: \[reads note\] "This note is about machine learning research..." AI: \[uses update\_tags to set tags: \["ai", "research", "neural-networks"\]\]

##### `remove_tags`

Remove tags from a note's frontmatter.

**Parameters:**

-   `path`: Path to the note
-   `tags`: List of tags to remove

##### `get_note_info`

Get metadata and statistics about a note without retrieving its full content.

**Parameters:**

-   `path`: Path to the note

**Returns:**

{ "path": "Projects/AI Research.md", "exists": true, "metadata": { "tags": \["ai", "research"\], "aliases": \[\], "frontmatter": {} }, "stats": { "size\_bytes": 4523, "word\_count": 823, "link\_count": 12 } }

#### Image Management

##### `read_image`

View an image from your vault. Images are automatically resized to a maximum width of 800px for optimal display in Claude Desktop.

**Parameters:**

-   `path`: Path to the image file (e.g., "Attachments/screenshot.png")

**Returns:**

-   A resized image object that can be viewed directly in Claude Desktop

**Supported formats:**

-   PNG, JPG/JPEG, GIF, BMP, WebP

##### `view_note_images`

Extract and view all images embedded in a note.

**Parameters:**

-   `path`: Path to the note containing images

**Returns:**

{ "note\_path": "Projects/Design Mockups.md", "image\_count": 3, "images": \[ { "path": "Attachments/mockup1.png", "alt\_text": "Homepage design", "image": "<FastMCP Image object>" } \] }

**Use cases:**

-   Analyze screenshots and diagrams in your notes
-   Review design mockups and visual documentation
-   Extract visual information for AI analysis

##### `list_tags`

List all unique tags used across your vault with usage statistics.

**Parameters:**

-   `include_counts` (default: `true`): Include usage count for each tag
-   `sort_by` (default: `"name"`): Sort by "name" or "count"

**Returns:**

{ "total\_tags": 25, "tags": \[ {"name": "project", "count": 42}, {"name": "project/web", "count": 15}, {"name": "project/mobile", "count": 8}, {"name": "meeting", "count": 38}, {"name": "idea", "count": 15} \] }

**Note:** Hierarchical tags are listed as separate entries, showing both parent and full paths.

**Performance Notes:**

-   Fast for small vaults (<1000 notes)
-   May take several seconds for large vaults
-   Uses concurrent batching for optimization

#### Link Management

**⚡ Performance Note:** Link management tools have been heavily optimized in v1.1.5:

-   **84x faster** link validity checking
-   **96x faster** broken link detection
-   **2x faster** backlink searches
-   Includes automatic caching and batch processing

##### `get_backlinks`

Find all notes that link to a specific note.

**Parameters:**

-   `path`: Path to the note to find backlinks for
-   `include_context` (default: `true`): Whether to include text context around links
-   `context_length` (default: `100`): Number of characters of context to include

**Returns:**

{ "target\_note": "Projects/AI Research.md", "backlink\_count": 5, "backlinks": \[ { "source\_path": "Daily/2024-01-15.md", "link\_text": "AI Research", "link\_type": "wiki", "context": "...working on the \[\[AI Research\]\] project today..." } \] }

**Use cases:**

-   Understanding which notes reference a concept or topic
-   Discovering relationships between notes
-   Building a mental map of note connections

##### `get_outgoing_links`

List all links from a specific note.

**Parameters:**

-   `path`: Path to the note to extract links from
-   `check_validity` (default: `false`): Whether to check if linked notes exist

**Returns:**

{ "source\_note": "Projects/Overview.md", "link\_count": 8, "links": \[ { "path": "Projects/AI Research.md", "display\_text": "AI Research", "type": "wiki", "exists": true } \] }

**Use cases:**

-   Understanding what a note references
-   Checking note dependencies before moving/deleting
-   Exploring the structure of index or hub notes

##### `find_broken_links`

Find all broken links in the vault, a specific directory, or a single note.

**Parameters:**

-   `directory` (optional): Specific directory to check (defaults to entire vault)
-   `single_note` (optional): Check only this specific note for broken links

**Returns:**

{ "directory": "/", "broken\_link\_count": 3, "affected\_notes": 2, "broken\_links": \[ { "source\_path": "Projects/Overview.md", "broken\_link": "Projects/Old Name.md", "link\_text": "Old Project", "link\_type": "wiki" } \] }

**Use cases:**

-   After renaming or deleting notes
-   Regular vault maintenance
-   Before reorganizing folder structure

### Testing

#### Running Tests

\# Run all tests python tests/run\_tests.py \# Or with pytest directly pytest tests/

Tests create temporary vaults for isolation and don't require a running Obsidian instance.

#### Testing with MCP Inspector

1.  **Set your vault path:**
    
    export OBSIDIAN\_VAULT\_PATH="/path/to/your/vault"
    
2.  **Run the MCP Inspector:**
    
    npx @modelcontextprotocol/inspector python -m obsidian\_mcp.server
    
3.  **Open the Inspector UI** at `http://localhost:5173`
4.  **Test the tools** interactively with your actual vault

### Integration with Claude Desktop

For development installations, see the [Development Installation](https://github.com/that0n3guy/ObsidianPilot/blob/main/#development-installation) section above.

### Enhanced Error Handling

The server provides detailed, actionable error messages to help AI systems recover from errors:

#### Example Error Messages

**Invalid Path**:

Invalid note path: '../../../etc/passwd'. Valid paths must: 1) End with .md or .markdown, 2) Use forward slashes (e.g., 'folder/note.md'), 3) Not contain '..' or start with '/', 4) Not exceed 255 characters. Example: 'Daily/2024-01-15.md' or 'Projects/My Project.md'

**Empty Search Query**:

Search query cannot be empty. Valid queries: 1) Keywords: 'machine learning', 2) Tags: 'tag:#project', 3) Paths: 'path:Daily/', 4) Combined: 'tag:#urgent TODO'

**Invalid Date Parameters**:

Invalid date\_type: 'invalid'. Must be either 'created' or 'modified'. Use 'created' to find notes by creation date, 'modified' for last edit date

### Troubleshooting

#### "Vault not found" error

-   Ensure the OBSIDIAN\_VAULT\_PATH environment variable is set correctly
-   Verify the path points to an existing Obsidian vault directory
-   Check that you have read/write permissions for the vault directory

#### Tags not showing up

-   Ensure tags are properly formatted (with or without # prefix)
-   Tags in frontmatter should be in YAML array format: `tags: [tag1, tag2]`
-   Inline tags should use the # prefix: `#project #urgent`
-   Tags inside code blocks are automatically excluded

#### "File too large" error

-   The server has a 10MB limit for note files and 50MB for images
-   This prevents memory issues with very large files
-   Consider splitting large notes into smaller ones

#### "Module not found" error

-   Ensure your virtual environment is activated
-   Run from the project root: `python -m obsidianpilot.server`
-   Verify all dependencies are installed: `pip install -r requirements.txt`

#### Empty results when listing notes

-   Specify a directory when using `list_notes` (e.g., "Daily", "Projects")
-   Root directory listing requires recursive implementation
-   Check if notes are in subdirectories

#### Tags not updating

-   Ensure notes have YAML frontmatter section for frontmatter tags
-   Frontmatter must include a `tags:` field (even if empty)
-   The server now properly reads both frontmatter tags and inline hashtags

### Best Practices for AI Assistants

#### Preventing Data Loss

1.  **Always read before updating**: The `update_note` tool REPLACES content by default
2.  **Use append mode for additions**: When adding to existing notes, use `merge_strategy="append"`
3.  **Check note existence**: Use `read_note` to verify a note exists before modifying
4.  **Be explicit about overwrites**: Only use `overwrite=true` when intentionally replacing content

#### Recommended Workflows

**Safe note editing:**

1.  Read the existing note first
2.  Modify the content as needed
3.  Update with the complete new content

**Adding to daily notes:**

-   Use `merge_strategy="append"` to add entries without losing existing content
-   Use `edit_note_section` to add content to specific sections (like "## Tasks" or "## Notes")

**Creating new notes:**

-   Use `create_note` with `overwrite=false` (default) to prevent accidental overwrites
-   Add relevant tags to maintain organization
-   Use `list_tags` to see existing tags and avoid creating duplicates

**Organizing with tags:**

-   Check existing tags with `list_tags` before creating new ones
-   Maintain consistent naming (e.g., use "project" not "projects")
-   Use tags to enable powerful search and filtering

### Security Considerations

-   **Vault path access** - The server only accesses the specified vault directory
-   The server validates all paths to prevent directory traversal attacks
-   File operations are restricted to the vault directory
-   Large files are rejected to prevent memory exhaustion
-   Path validation prevents access to system files

### Development

#### Code Style

-   Uses FastMCP framework for MCP implementation
-   Pydantic models for type safety and validation
-   Modular architecture with separated concerns
-   Comprehensive error handling and user-friendly messages

#### Adding New Tools

1.  Create tool function in appropriate module under `src/tools/`
2.  Add Pydantic models if needed in `src/models/`
3.  Register the tool in `src/server.py` with the `@mcp.tool()` decorator
4.  Include comprehensive docstrings
5.  Add tests in `tests/`
6.  Test with MCP Inspector before deploying

### Changelog

#### v2.0.3 (2025-06-27)

-   ✏️ **Token-efficient section editing** - New `edit_note_section` tool for precise content insertion and updates
-   🎯 **Five edit operations** - Insert before/after headings, replace sections, append to sections, or edit headings only
-   📍 **Smart section detection** - Case-insensitive markdown heading matching with hierarchy support
-   🔧 **Create missing sections** - Optionally create sections if they don't exist
-   📝 **Preserve note structure** - Edit specific parts without rewriting entire notes
-   🔍 **Precise text replacement** - New `edit_note_content` tool for exact text search and replace
-   🛡️ **Frontmatter preservation** - Automatically detects and maintains YAML frontmatter during all edits
-   🐛 **FastMCP compatibility** - Fixed deprecated import warnings and updated dependencies
-   📚 **Windows setup guide** - Comprehensive installation instructions for Windows environments

#### v2.0.2 (2025-01-24)

-   🎯 **Simplified architecture** - Removed memory index, SQLite is now the only search method
-   🔍 **Search transparency** - Added metadata to search results (total\_count, truncated, limit)
-   ⚙️ **Configurable search limits** - Exposed max\_results parameter (1-500, default 50)
-   🧹 **Reduced tool clutter** - Removed unnecessary index management tools
-   📝 **Reasoning-friendly improvements** - Enhanced all tools with proper Field annotations and comprehensive docstrings
-   🚀 **Better AI reasoning** - Added "When to use" and "When NOT to use" sections to all tools
-   ⚡ **Performance notes** - Added explicit performance guidance for expensive operations
-   🔧 **Cleaner codebase** - Removed ~500 lines of memory index code, reducing maintenance burden

#### v2.0.0 (2025-01-24)

-   🚀 **Complete architecture overhaul** - Migrated from REST API to direct filesystem access
-   ⚡ **5x faster searches** with persistent SQLite indexing that survives between sessions
-   🖼️ **Image support** - View and analyze images from your vault with automatic resizing
-   🔍 **Regex power search** - Find complex patterns with optimized streaming
-   🗂️ **Property search** - Query notes by frontmatter properties with advanced operators
-   🎯 **One-command setup** - Auto-configure Claude Desktop with `uvx --from ObsidianPilot ObsidianPilot-configure`
-   📦 **90% less memory usage** - Efficient streaming architecture
-   🔄 **No plugins required** - Works offline without needing Obsidian to be running
-   ✨ **Incremental indexing** - Only re-indexes changed files
-   🔧 **Migration support** - Automatically detects and migrates old REST API configs
-   🏷️ **Enhanced hierarchical tag support** - Full support for Obsidian's nested tag system
    -   Search parent tags to find all children (e.g., `tag:project` finds `project/web`)
    -   Search child tags across any hierarchy (e.g., `tag:web` finds `project/web`, `design/web`)
    -   Exact hierarchical matching (e.g., `tag:project/web`)
-   🔍 **Improved metadata handling** - Better alignment with Obsidian's property system
    -   Automatic migration of legacy properties (`tag`→`tags`, `alias`→`aliases`)
    -   Array/list property searching (find items within arrays)
    -   Date property comparisons with ISO format support
    -   Numeric comparisons for array lengths
-   📝 **AI-friendly tool definitions** - Updated all tool descriptions for better LLM understanding
    -   Added hierarchical tag examples to all tag-related tools
    -   Enhanced property search documentation
    -   Clearer parameter descriptions following MCP best practices

#### v1.1.8 (2025-01-15)

-   🔧 Fixed FastMCP compatibility issue that prevented PyPI package from running
-   📦 Updated to FastMCP 2.8.1 for better stability
-   🐛 Fixed Pydantic V2 deprecation warnings (migrated to @field\_validator)
-   ✨ Changed FastMCP initialization to use 'instructions' parameter
-   🚀 Improved compatibility with uvx and pipx installation methods

#### v1.1.7 (2025-01-10)

-   🔄 Changed default API endpoint to HTTP (`http://127.0.0.1:27123`) for easier setup
-   📝 Updated documentation to reflect HTTP as default, HTTPS as optional
-   🔧 Added note about automatic trailing slash handling in URLs
-   ✨ Improved first-time user experience with zero-configuration setup

#### v1.1.6 (2025-01-10)

-   🐛 Fixed timeout errors when creating or updating large notes
-   ⚡ Added graceful timeout handling for better reliability with large content
-   🔧 Improved error reporting to prevent false failures on successful operations

#### v1.1.5 (2025-01-09)

-   ⚡ **Massive performance optimization for link management:**
    -   84x faster link validity checking
    -   96x faster broken link detection
    -   2x faster backlink searches
    -   Added automatic caching and batch processing
-   🔧 Optimized concurrent operations for large vaults
-   📝 Enhanced documentation for performance considerations

#### v1.1.4 (2025-01-09)

-   🔗 Added link management tools for comprehensive vault analysis:
    -   `get_backlinks` - Find all notes linking to a specific note
    -   `get_outgoing_links` - List all links from a note with validity checking
    -   `find_broken_links` - Identify broken links for vault maintenance
-   🔧 Fixed URL construction to support both HTTPS (default) and HTTP endpoints
-   📝 Enhanced link parsing to handle both wiki-style and markdown links
-   ⚡ Optimized backlink search to handle various path formats

#### v1.1.3 (2025-01-09)

-   🐛 Fixed search\_by\_date to properly find notes modified today (days\_ago=0)
-   ✨ Added list\_folders tool for exploring vault folder structure
-   ✨ Added create\_folder tool that creates full folder hierarchies
-   ✨ Added move\_folder tool for bulk folder operations
-   ✨ Added update\_tags tool for AI-driven tag management
-   🐛 Fixed tag reading to properly handle both frontmatter and inline hashtags
-   ✨ Added list\_tags tool to discover existing tags with usage statistics
-   ⚡ Optimized performance with concurrent batching for large vaults
-   📝 Improved documentation and error messages following MCP best practices
-   🎯 Enhanced create\_note to encourage tag usage for better organization

#### v1.1.2 (2025-01-09)

-   Fixed PyPI package documentation

#### v1.1.1 (2025-01-06)

-   Initial PyPI release

### Publishing (for maintainers)

To publish a new version to PyPI:

\# 1. Update version in pyproject.toml \# 2. Clean old builds rm -rf dist/ build/ \*.egg-info/ \# 3. Build the package python -m build \# 4. Check the package twine check dist/\* \# 5. Upload to PyPI twine upload dist/\* -u \_\_token\_\_ -p $PYPI\_API\_KEY \# 6. Create and push git tag git tag -a v2.0.2 -m "Release version 2.0.2" git push origin v2.0.2

Users can then install and run with:

\# Using uvx (recommended - no installation needed) uvx ObsidianPilot \# Or install globally with pipx pipx install ObsidianPilot ObsidianPilot \# Or with pip pip install ObsidianPilot ObsidianPilot

### Configuration

#### Performance and Indexing

The server now includes a **persistent search index** using SQLite for dramatically improved performance:

##### Key Features:

-   **Instant startup** - No need to rebuild index on every server start
-   **Incremental updates** - Only re-indexes files that have changed
-   **60x faster searches** - SQLite queries are much faster than scanning all files
-   **Lower memory usage** - Files are loaded on-demand rather than all at once

##### Configuration Options:

Set these environment variables to customize behavior:

\# Set logging level (default: INFO, options: DEBUG, INFO, WARNING, ERROR) export OBSIDIAN\_LOG\_LEVEL=DEBUG

The search index is stored in your vault at `.obsidian/mcp-search-index.db`.

#### Performance Notes

-   **Search indexing** - With persistent index, only changed files are re-indexed
-   **Concurrent operations** - File operations use async I/O for better performance
-   **Large vaults** - Incremental indexing makes large vaults (10,000+ notes) usable
-   **Image handling** - Images are automatically resized to prevent memory issues

#### Migration from REST API Version

If you were using a previous version that required the Local REST API plugin:

1.  **You no longer need the Obsidian Local REST API plugin** - This server now uses direct filesystem access
2.  Replace `OBSIDIAN_REST_API_KEY` with `OBSIDIAN_VAULT_PATH` in your configuration
3.  Remove any `OBSIDIAN_API_URL` settings
4.  The new version is significantly faster and more reliable
5.  All features work offline without requiring Obsidian to be running

### Contributing

1.  Fork the repository
2.  Create a feature branch (`git checkout -b feature/amazing-tool`)
3.  Write tests for new functionality
4.  Ensure all tests pass
5.  Commit your changes (`git commit -m 'Add amazing tool'`)
6.  Push to the branch (`git push origin feature/amazing-tool`)
7.  Open a Pull Request

### License

MIT License - see LICENSE file for details

### Acknowledgments

-   **[Nate Strong](https://github.com/natestrong/obsidian-mcp)** for creating the original obsidian-mcp foundation that made ObsidianPilot possible
-   [Anthropic](https://anthropic.com/) for creating the Model Context Protocol
-   [Obsidian](https://obsidian.md/) team for the amazing note-taking app
-   [coddingtonbear](https://github.com/coddingtonbear) for the original Local REST API plugin (no longer required)
-   [dsp-ant](https://github.com/dsp-ant) for the FastMCP framework