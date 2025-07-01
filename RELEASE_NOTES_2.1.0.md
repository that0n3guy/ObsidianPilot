# ObsidianPilot v2.1.0 Release Notes

## 🚀 Revolutionary Search Performance: From Hanging to Instant

### Overview
Version 2.1.0 delivers the most significant performance improvement in ObsidianPilot's history. This release completely eliminates search timeout issues on large vaults by replacing slow `LIKE '%query%'` SQL queries with modern SQLite FTS5 full-text search indexing, delivering 100-1000x performance improvements.

### 🎯 Critical Issues Resolved
- **❌ Search Hanging Fixed**: Queries like `"project"` and `"Eide Bailly OR CPA OR Pattern"` that hung indefinitely on large vaults (1800+ notes) **now complete in under 0.5 seconds**
- **❌ Tool Timeouts Eliminated**: `search_notes_tool`, `search_by_regex_tool`, and `search_by_property_tool` no longer timeout
- **❌ Large Vault Limitations Removed**: Vaults with 1000+ notes now have instant search performance
- **❌ Memory Issues Resolved**: Efficient indexing prevents memory overload during search operations

### ✨ New Features

#### Enhanced Search Tools
- **`search_notes`**: Primary search tool now uses lightning-fast FTS5 with boolean operator support
- **`search_by_field`**: Target specific fields (filename, tags, properties, content) - internal optimization
- **`rebuild_search_index`**: Rebuild search index when needed
- **`get_search_stats`**: Monitor search index status and performance

#### Advanced Search Capabilities
- **Boolean Operators**: Support for AND, OR, NOT operations
  - Example: `"python AND tutorial"`, `"Eide Bailly OR CPA OR accounting"`
- **Phrase Search**: Automatic phrase detection for multi-word queries
  - Example: `"machine learning"` searches for exact phrase
- **Complex Queries**: Nested boolean expressions
  - Example: `"(python OR ruby) AND tutorial"`

#### Background Indexing & Optimization
- **Automatic Indexing**: Index builds in background on first startup
- **File Change Tracking**: Automatic index updates when notes are created/modified
- **Smart Monitoring**: 10-second file change detection (reduced from 60 seconds)
- **Folder Exclusions**: Automatically skips `.trash/` and `.obsidian/` folders for cleaner results
- **Timeout Protection**: Graceful handling of large vault indexing without blocking AI interactions
- **Background Rebuilds**: `rebuild_search_index_tool` returns immediately while rebuilding in background

#### Search Performance
- **SQLite FTS5**: Modern full-text search with proper ranking
- **Relevance Scoring**: Results ranked by relevance with scoring
- **Context Snippets**: Highlighted search contexts with `<mark>` tags
- **Pagination Support**: Efficient result streaming for large result sets

### 🔧 Technical Improvements

#### New Files Added
- `obsidianpilot/utils/fts_search.py`: Core FTS5 search implementation
- `obsidianpilot/tools/fast_search.py`: Fast search tool implementations
- `obsidianpilot/utils/index_updater.py`: Automatic index updating system

#### Database Integration
- **FTS5 Virtual Tables**: Advanced full-text search capabilities
- **Metadata Tracking**: File modification time and size tracking
- **Index Storage**: Efficient storage in `.obsidian/fts-search-index.db`

#### Search Index Features
- **Porter Stemming**: Improved word matching with stemming
- **Unicode Support**: Full Unicode text normalization
- **Diacritic Removal**: Search works regardless of accents
- **Case Insensitive**: Automatic case-insensitive matching

### 🔧 Enhanced Legacy Search Tools

#### Automatic Performance Optimization
All existing search tools now include smart performance enhancements:

**`search_notes_tool` (Now Fully Fast)**:
- **FTS5 backend**: Now uses SQLite FTS5 full-text search as primary implementation
- **Boolean operators**: Full support for AND, OR, NOT complex queries
- **Legacy compatibility**: Maintains support for tag:, path:, and property: prefixes
- **100-1000x faster**: Replaces old slow implementation entirely

**`search_by_property_tool` (Fast FTS5 Backend)**:
- **Primary method**: Uses fast FTS5 search for `=`, `contains`, `exists` operators
- **Complex fallback**: Advanced operators (`>`, `<`, `>=`, `<=`, `!=`) use manual search with warnings
- **Smart value extraction**: Extracts actual property values from search context
- **Performance transparency**: Clear indication of which search method was used

**`search_by_regex_tool` (Timeout Protection)**:
- **Smart timeouts**: 20-30s timeouts based on vault size prevent hanging
- **Alternative suggestions**: Detects simple patterns and suggests fast search equivalents
- **Result optimization**: Automatically limits results for large vaults (1000+ notes = 10 max results)
- **Helpful errors**: Timeout messages include specific fast search alternatives

### 🔄 Backward Compatibility
- **Zero breaking changes**: All existing search tools maintain exact same API
- **Tool consolidation**: `search_notes_tool` now uses the fast FTS5 implementation directly (no more separate `fast_search_notes_tool`)
- **Legacy syntax support**: tag:, path:, and property: prefixes continue to work seamlessly
- **Existing configurations**: All MCP configurations continue to work without modification
- **Progressive enhancement**: All search operations now benefit from FTS5 performance

### 📊 Performance Benchmarks
- **Before**: Search queries hanging indefinitely on 1800+ note vaults
- **After**: Search completion in 0.008-0.461 seconds
- **Index Size**: ~1818 files indexed from 1823 total files
- **Index Build Time**: ~2-5 minutes for 1800+ files (one-time background process)

### 🛠️ Usage Recommendations

#### Primary Search Tool
- **`search_notes_tool`**: Now the unified, ultra-fast search solution for all vault sizes
- **Boolean queries**: Use AND, OR, NOT for complex searches like `"python AND (tutorial OR guide)"`
- **Legacy syntax**: Continue using tag:, path:, and property: prefixes as before
- **Phrase search**: Multi-word queries automatically treated as phrases

#### Specialized Tools
- **`search_by_property_tool`**: For complex property comparisons (>, <, >=, etc.)
- **`search_by_regex_tool`**: For pattern matching and complex text structures
- **`search_by_date_tool`**: For date-based filtering

### 📋 Migration Notes
No migration required - this is an additive feature. The fast search index will build automatically in the background on first use.

### 🐛 Fixes
- Fixed missing logger import in server.py that caused NameError
- Resolved metadata handling for NoteMetadata objects vs dictionaries
- Added proper error handling for FTS5 query syntax

### 🔮 Future Enhancements
- Field-specific boolean queries
- Search history and suggestions
- Index optimization and compression
- Real-time search as you type

---

**Installation**: `pip install -e .` or build from source
**Testing**: Run `python3 test_fast_search.py` to verify fast search functionality
**Index Location**: `.obsidian/fts-search-index.db` (automatically created)

This release represents a major step forward in making ObsidianPilot suitable for large knowledge bases and professional workflows.