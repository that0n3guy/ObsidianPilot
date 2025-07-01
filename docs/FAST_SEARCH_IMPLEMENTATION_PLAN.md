# Fast Search Implementation Plan for ObsidianPilot

## Problem Statement

The current search implementation in ObsidianPilot has critical performance issues:
- Uses `LIKE '%query%'` SQL queries without indexes, causing full table scans
- No support for boolean operators (AND, OR, NOT)
- Searches through entire note content for every query
- Can hang indefinitely on large vaults (1000+ notes)
- Special searches (tag, path, property) read ALL notes into memory

## Proposed Solution: SQLite FTS5 Full-Text Search

### Why FTS5?

1. **Already Available**: Built into SQLite, no new dependencies
2. **Extremely Fast**: 100-1000x faster than LIKE queries
3. **Rich Features**: Boolean operators, phrase search, ranking
4. **Production Ready**: Used by many large applications
5. **Low Memory**: Efficient indexing and search

### Alternative Options Considered

| Solution | Pros | Cons | Decision |
|----------|------|------|----------|
| **SQLite FTS5** | Built-in, fast, feature-rich | None significant | ✅ **Recommended** |
| Whoosh | Pure Python, no C deps | Slower, separate index files | ❌ |
| Tantivy | Extremely fast (Rust) | Requires compilation, new dependency | ❌ |
| MeiliSearch | Very fast, great features | Requires separate server | ❌ |

## Implementation Plan

### Phase 1: Basic FTS5 Implementation (Critical Fix)

**Goal**: Fix the hanging search issue immediately

#### 1.1 Create FTS5 Virtual Table

```python
CREATE VIRTUAL TABLE notes_fts USING fts5(
    filepath UNINDEXED,     -- Don't index for search
    filename,               -- Note name without extension
    content,               -- Full note content
    tags,                  -- Space-separated tags
    properties,            -- Key:value pairs from frontmatter
    tokenize = 'porter unicode61 remove_diacritics 1'
);
```

#### 1.2 Migration from Existing Index

```python
async def migrate_to_fts5(self):
    """One-time migration from current index to FTS5"""
    # Create FTS5 table
    await self.create_fts_table()
    
    # Migrate existing data
    cursor = await self.db.execute(
        "SELECT filepath, content FROM file_index"
    )
    
    async for row in cursor:
        filepath, content = row
        await self.update_fts_index(filepath, content)
    
    # Create triggers for automatic updates
    await self.create_fts_triggers()
```

#### 1.3 Basic Search Implementation

```python
async def search_fast(
    self, 
    query: str, 
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Fast full-text search with FTS5"""
    
    cursor = await self.db.execute("""
        SELECT 
            filepath,
            snippet(notes_fts, 2, '<mark>', '</mark>', '...', 30) as snippet,
            rank
        FROM notes_fts
        WHERE notes_fts MATCH ?
        ORDER BY rank
        LIMIT ? OFFSET ?
    """, (query, limit, offset))
    
    results = []
    async for row in cursor:
        results.append({
            "path": row[0],
            "context": row[1],
            "score": -row[2]  # rank is negative in FTS5
        })
    
    return results
```

### Phase 2: Enhanced Search Features

#### 2.1 Query Parser

Support for various search syntaxes:

```python
class SearchQueryParser:
    def parse(self, query: str) -> str:
        """Transform user query to FTS5 syntax"""
        
        # Boolean operators
        query = self._handle_boolean_operators(query)
        
        # Field-specific search
        query = self._handle_field_search(query)
        
        # Smart phrases
        query = self._handle_phrases(query)
        
        return query
    
    def _handle_boolean_operators(self, query: str) -> str:
        # Convert common patterns
        replacements = {
            " || ": " OR ",
            " && ": " AND ",
            " -": " NOT ",
            " !": " NOT "
        }
        for old, new in replacements.items():
            query = query.replace(old, new)
        return query
```

#### 2.2 Supported Search Syntax

| Syntax | Example | Description |
|--------|---------|-------------|
| Boolean AND | `python AND tutorial` | Both terms required |
| Boolean OR | `python OR javascript` | Either term |
| Boolean NOT | `python NOT snake` | Exclude term |
| Phrase | `"machine learning"` | Exact phrase |
| Prefix | `obsid*` | Starts with |
| Field | `title:README` | Search specific field |
| Grouping | `(python OR ruby) AND tutorial` | Complex queries |

#### 2.3 Special Searches Migration

Integrate tag, path, and property searches into FTS5:

```python
async def search_by_tag(self, tag: str) -> List[Dict]:
    # Use FTS5 instead of scanning all notes
    fts_query = f'tags:"{tag}" OR tags:"{tag}/*"'
    return await self.search_fast(fts_query)

async def search_by_path(self, path: str) -> List[Dict]:
    fts_query = f'filepath:"{path}*"'
    return await self.search_fast(fts_query)
```

### Phase 3: Performance Optimizations

#### 3.1 Incremental Index Updates

```python
async def update_file(self, filepath: str, content: str, metadata: dict):
    """Update single file in FTS index"""
    # Extract metadata
    filename = Path(filepath).stem
    tags = ' '.join(metadata.get('tags', []))
    properties = self._format_properties(metadata)
    
    # Update FTS5 index
    await self.db.execute("""
        INSERT OR REPLACE INTO notes_fts 
        (filepath, filename, content, tags, properties)
        VALUES (?, ?, ?, ?, ?)
    """, (filepath, filename, content, tags, properties))
```

#### 3.2 Search Result Streaming

```python
async def search_stream(
    self, 
    query: str, 
    batch_size: int = 10
) -> AsyncIterator[List[Dict]]:
    """Stream search results in batches"""
    offset = 0
    
    while True:
        results = await self.search_fast(
            query, 
            limit=batch_size, 
            offset=offset
        )
        
        if not results:
            break
            
        yield results
        offset += batch_size
```

#### 3.3 Search Caching

```python
class SearchCache:
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache = {}  # LRU cache
        self.max_size = max_size
        self.ttl = ttl
    
    async def get_or_search(self, query: str) -> List[Dict]:
        cache_key = hashlib.md5(query.encode()).hexdigest()
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry['time'] < self.ttl:
                return entry['results']
        
        # Perform search
        results = await self.search_fast(query)
        
        # Cache results
        self.cache[cache_key] = {
            'results': results,
            'time': time.time()
        }
        
        return results
```

### Phase 4: Advanced Features (Future)

#### 4.1 Fuzzy Search
- Implement Levenshtein distance for typo tolerance
- "Did you mean?" suggestions

#### 4.2 Search Analytics
- Track popular searches
- Search performance metrics
- Query optimization hints

#### 4.3 Advanced Ranking
- TF-IDF scoring
- Boost recent documents
- Custom ranking functions

## Migration Strategy

1. **Backward Compatibility**: Keep existing search working during migration
2. **Feature Flag**: Add `use_fts5_search` configuration option
3. **Gradual Rollout**: 
   - Phase 1: Optional beta feature
   - Phase 2: Default for new installations
   - Phase 3: Migrate existing users

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Search time (1000 notes) | 10-60s | <0.1s |
| Boolean operator support | No | Yes |
| Memory usage | High | Low |
| Result quality | Basic | Ranked |

## Implementation Timeline

- **Week 1**: Basic FTS5 implementation (Phase 1)
- **Week 2**: Query parser and enhanced search (Phase 2)
- **Week 3**: Performance optimizations (Phase 3)
- **Week 4**: Testing and documentation

## Code Organization

```
obsidianpilot/
├── utils/
│   ├── search/
│   │   ├── __init__.py
│   │   ├── fts_index.py      # FTS5 index management
│   │   ├── query_parser.py   # Query parsing logic
│   │   ├── search_cache.py   # Caching layer
│   │   └── migrations.py     # Index migration
│   └── persistent_index.py   # Keep for compatibility
└── tools/
    └── search_discovery.py   # Updated to use new search
```

## Testing Strategy

1. **Performance Tests**: Benchmark against current implementation
2. **Query Tests**: Verify all search syntaxes work correctly
3. **Migration Tests**: Ensure smooth upgrade path
4. **Edge Cases**: Large vaults, special characters, Unicode

## Documentation Updates

1. Update search tool documentation with new syntax
2. Add search syntax guide for users
3. Migration guide for existing installations
4. Performance tuning guide

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing searches | Keep old search as fallback |
| Migration failures | Automatic rollback, manual recovery |
| Performance regression | Extensive benchmarking before release |
| User confusion | Clear documentation, examples |

## Next Steps

1. Review and approve this plan
2. Create feature branch `feature/fts5-search`
3. Implement Phase 1 (critical fix)
4. Test with large vaults
5. Deploy as beta feature