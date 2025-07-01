"""Fast full-text search implementation using SQLite FTS5."""

import asyncio
import aiosqlite
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator
from ..utils.filesystem import get_vault

logger = logging.getLogger(__name__)


class FTSSearchIndex:
    """Fast full-text search using SQLite FTS5 virtual tables."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the FTS5 search index."""
        if self._initialized:
            return
            
        self.db = await aiosqlite.connect(self.db_path)
        await self._create_fts_tables()
        self._initialized = True
        logger.info("FTS5 search index initialized")
        
    async def close(self):
        """Close the database connection."""
        if self.db:
            await self.db.close()
            self._initialized = False
            
    async def _create_fts_tables(self):
        """Create FTS5 virtual table and supporting tables."""
        
        # Create FTS5 virtual table for fast search
        await self.db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                filepath UNINDEXED,     -- File path (not searchable)
                filename,               -- Note filename without extension
                content,               -- Full note content
                tags,                  -- Space-separated tags
                properties,            -- Frontmatter properties as text
                tokenize = 'porter unicode61 remove_diacritics 1'
            )
        """)
        
        # Create metadata table for additional info
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS notes_metadata (
                filepath TEXT PRIMARY KEY,
                mtime REAL,
                size INTEGER,
                last_indexed REAL
            )
        """)
        
        # Create index on metadata table
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_mtime 
            ON notes_metadata(mtime)
        """)
        
        await self.db.commit()
        
    async def index_file(self, filepath: str, content: str, metadata: Dict[str, Any]):
        """Index a single file in the FTS5 table."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Extract components
            filename = Path(filepath).stem
            
            # Handle metadata as NoteMetadata object
            if hasattr(metadata, 'tags'):
                tags = ' '.join(metadata.tags if metadata.tags else [])
            else:
                tags = ''
            
            # Format properties as searchable text
            properties = []
            if hasattr(metadata, 'frontmatter') and metadata.frontmatter:
                for key, value in metadata.frontmatter.items():
                    if key != 'tags':  # Tags handled separately
                        if isinstance(value, list):
                            properties.append(f"{key}:{' '.join(str(v) for v in value)}")
                        else:
                            properties.append(f"{key}:{value}")
            properties_text = ' '.join(properties)
            
            # Delete existing entry first (FTS5 doesn't support PRIMARY KEY for OR REPLACE)
            await self.db.execute("DELETE FROM notes_fts WHERE filepath = ?", (filepath,))
            
            # Insert new entry in FTS5 table
            await self.db.execute("""
                INSERT INTO notes_fts 
                (filepath, filename, content, tags, properties)
                VALUES (?, ?, ?, ?, ?)
            """, (filepath, filename, content, tags, properties_text))
            
            # Update metadata
            await self.db.execute("""
                INSERT OR REPLACE INTO notes_metadata
                (filepath, mtime, size, last_indexed)
                VALUES (?, ?, ?, ?)
            """, (filepath, time.time(), len(content), time.time()))
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error indexing file {filepath}: {e}")
            raise
            
    async def remove_file(self, filepath: str):
        """Remove a file from the FTS5 index."""
        if not self._initialized:
            return
            
        await self.db.execute("DELETE FROM notes_fts WHERE filepath = ?", (filepath,))
        await self.db.execute("DELETE FROM notes_metadata WHERE filepath = ?", (filepath,))
        await self.db.commit()
        
    async def search(
        self, 
        query: str, 
        limit: int = 50, 
        offset: int = 0,
        snippet_length: int = 30
    ) -> List[Dict[str, Any]]:
        """Perform fast full-text search using FTS5."""
        if not self._initialized:
            await self.initialize()
            
        try:
            # Transform query for FTS5
            fts_query = self._transform_query(query)
            logger.debug(f"Transformed query: '{query}' -> FTS5 query: '{fts_query}'")
            
            # Perform search with ranking
            cursor = await self.db.execute("""
                SELECT 
                    filepath,
                    snippet(notes_fts, 2, '<mark>', '</mark>', '...', ?) as snippet,
                    rank,
                    filename
                FROM notes_fts
                WHERE notes_fts MATCH ?
                ORDER BY rank
                LIMIT ? OFFSET ?
            """, (snippet_length, fts_query, limit, offset))
            
            results = []
            rows = await cursor.fetchall()
            
            for row in rows:
                filepath, snippet, rank, filename = row
                results.append({
                    "path": filepath,
                    "filename": filename,
                    "context": snippet,
                    "score": -rank,  # FTS5 rank is negative, flip for intuitive scoring
                    "rank": len(results) + offset + 1
                })
                
            return results
            
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}")
            # Fall back to simple search if FTS5 query fails
            return await self._simple_search(query, limit, offset)
            
    def _transform_query(self, query: str) -> str:
        """Transform user query to FTS5 syntax."""
        if not query.strip():
            raise ValueError("Search query cannot be empty")
            
        # Handle quoted phrases
        if query.startswith('"') and query.endswith('"'):
            return query  # Already a phrase
            
        # Handle boolean operators (case insensitive)
        query = query.replace(' or ', ' OR ')
        query = query.replace(' and ', ' AND ')
        query = query.replace(' not ', ' NOT ')
        
        # Handle simple multi-word queries as phrases for better results
        if (' OR ' not in query and ' AND ' not in query and ' NOT ' not in query 
            and ' ' in query.strip() and not query.startswith('"')):
            # Convert "machine learning" to "machine learning" for phrase search
            return f'"{query.strip()}"'
            
        return query.strip()
        
    async def _simple_search(
        self, 
        query: str, 
        limit: int, 
        offset: int
    ) -> List[Dict[str, Any]]:
        """Fallback simple search if FTS5 query fails."""
        query_lower = query.lower()
        
        cursor = await self.db.execute("""
            SELECT filepath, filename, content
            FROM notes_fts
            WHERE content LIKE ?
            LIMIT ? OFFSET ?
        """, (f"%{query_lower}%", limit, offset))
        
        results = []
        rows = await cursor.fetchall()
        
        for i, row in enumerate(rows):
            filepath, filename, content = row
            
            # Create simple context
            content_lower = content.lower()
            match_pos = content_lower.find(query_lower)
            if match_pos >= 0:
                start = max(0, match_pos - 50)
                end = min(len(content), match_pos + len(query) + 50)
                context = content[start:end].strip()
                if start > 0:
                    context = "..." + context
                if end < len(content):
                    context = context + "..."
            else:
                context = content[:100].strip() + "..."
                
            results.append({
                "path": filepath,
                "filename": filename,
                "context": context,
                "score": 1.0,
                "rank": i + offset + 1
            })
            
        return results
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get search index statistics."""
        if not self._initialized:
            await self.initialize()
            
        # Get total indexed files
        cursor = await self.db.execute("SELECT COUNT(*) FROM notes_fts")
        total_files = (await cursor.fetchone())[0]
        
        # Get total content size
        cursor = await self.db.execute("SELECT SUM(size) FROM notes_metadata")
        total_size = (await cursor.fetchone())[0] or 0
        
        # Get index freshness
        cursor = await self.db.execute("""
            SELECT 
                MIN(last_indexed) as oldest,
                MAX(last_indexed) as newest
            FROM notes_metadata
        """)
        row = await cursor.fetchone()
        oldest_index = row[0]
        newest_index = row[1]
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "oldest_index": oldest_index,
            "newest_index": newest_index,
            "index_age_seconds": time.time() - (newest_index or 0)
        }


class QueryParser:
    """Parse and validate search queries."""
    
    @staticmethod
    def parse_field_query(query: str) -> Dict[str, str]:
        """Parse field-specific queries like 'title:README' or 'tag:project'."""
        field_queries = {}
        
        # Split by spaces but preserve quoted phrases
        tokens = []
        in_quotes = False
        current_token = ""
        
        for char in query:
            if char == '"':
                in_quotes = not in_quotes
                current_token += char
            elif char == ' ' and not in_quotes:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char
                
        if current_token:
            tokens.append(current_token)
            
        # Parse field:value tokens
        remaining_tokens = []
        for token in tokens:
            if ':' in token and not token.startswith('"'):
                field, value = token.split(':', 1)
                field_queries[field.strip()] = value.strip()
            else:
                remaining_tokens.append(token)
                
        # Add remaining tokens as content search
        if remaining_tokens:
            field_queries['content'] = ' '.join(remaining_tokens)
            
        return field_queries
        
    @staticmethod
    def validate_query(query: str) -> tuple[bool, str]:
        """Validate search query."""
        if not query or not query.strip():
            return False, "Search query cannot be empty"
            
        if len(query) > 1000:
            return False, "Search query too long (max 1000 characters)"
            
        # Check for potential SQL injection (basic)
        dangerous_patterns = ['--', ';', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if pattern in query_upper:
                return False, f"Query contains potentially dangerous pattern: {pattern}"
                
        return True, ""


# Global FTS search instance
_fts_search: Optional[FTSSearchIndex] = None


async def get_fts_search() -> FTSSearchIndex:
    """Get or create the global FTS search instance."""
    global _fts_search
    
    if _fts_search is None:
        vault = get_vault()
        # Store FTS index alongside the vault
        fts_db_path = vault.vault_path / ".obsidian" / "fts-search-index.db"
        fts_db_path.parent.mkdir(exist_ok=True)
        
        _fts_search = FTSSearchIndex(str(fts_db_path))
        await _fts_search.initialize()
        
    return _fts_search


async def rebuild_fts_index():
    """Rebuild the entire FTS index from scratch."""
    fts = await get_fts_search()
    vault = get_vault()
    
    logger.info("Rebuilding FTS index...")
    
    # Clear existing index
    if fts._initialized:
        await fts.db.execute("DELETE FROM notes_fts")
        await fts.db.execute("DELETE FROM notes_metadata")
        await fts.db.commit()
    
    # Re-index all notes
    all_notes = await vault.list_notes(recursive=True)
    indexed_count = 0
    
    for note_info in all_notes:
        filepath = note_info["path"]
        
        # Skip files in .trash and .obsidian folders (handle both Windows \ and Unix / separators)
        filepath_normalized = filepath.replace('\\', '/')
        if (filepath_normalized.startswith('.trash/') or '/.trash/' in filepath_normalized or
            filepath_normalized.startswith('.obsidian/') or '/.obsidian/' in filepath_normalized):
            continue
            
        try:
            note = await vault.read_note(filepath)
            await fts.index_file(note.path, note.content, note.metadata)
            indexed_count += 1
            
            if indexed_count % 100 == 0:
                logger.info(f"Indexed {indexed_count} notes...")
                
        except Exception as e:
            logger.warning(f"Failed to index {note_info['path']}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            continue
    
    logger.info(f"FTS index rebuild complete. Indexed {indexed_count} notes.")
    return indexed_count