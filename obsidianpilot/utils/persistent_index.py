"""Persistent search index using SQLite for Obsidian vault."""

import os
import hashlib
import json
import asyncio
import aiosqlite
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PersistentSearchIndex:
    """SQLite-based persistent search index for efficient vault searching."""
    
    def __init__(self, vault_path: Path, index_path: Optional[Path] = None):
        """
        Initialize persistent search index.
        
        Args:
            vault_path: Path to the Obsidian vault
            index_path: Path to store the SQLite database (defaults to vault/.obsidian/search-index.db)
        """
        self.vault_path = vault_path
        
        # Default index location in .obsidian folder
        if index_path is None:
            obsidian_dir = vault_path / ".obsidian"
            obsidian_dir.mkdir(exist_ok=True)
            self.index_path = obsidian_dir / "mcp-search-index.db"
        else:
            self.index_path = index_path
            
        self.db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize database connection and create tables if needed."""
        self.db = await aiosqlite.connect(str(self.index_path))
        
        # Enable WAL mode for better concurrent access
        await self.db.execute("PRAGMA journal_mode=WAL")
        
        # Create tables
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS file_index (
                filepath TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                content_lower TEXT NOT NULL,
                mtime REAL NOT NULL,
                size INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                last_indexed REAL NOT NULL,
                metadata TEXT,
                line_offsets TEXT
            )
        """)
        
        # Check if we need to add line_offsets column (for existing databases)
        cursor = await self.db.execute("PRAGMA table_info(file_index)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'line_offsets' not in column_names:
            await self.db.execute("ALTER TABLE file_index ADD COLUMN line_offsets TEXT")
            logger.info("Added line_offsets column to existing database")
        
        # Create properties table for efficient property searches
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS file_properties (
                filepath TEXT NOT NULL,
                property_name TEXT NOT NULL,
                property_value TEXT,
                property_type TEXT,
                PRIMARY KEY (filepath, property_name),
                FOREIGN KEY (filepath) REFERENCES file_index(filepath) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for faster searching
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mtime ON file_index(mtime)
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_size ON file_index(size)
        """)
        
        # Create indexes for property searches
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_name ON file_properties(property_name)
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_value ON file_properties(property_value)
        """)
        
        # Create FTS5 virtual table for full-text search
        await self.db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS file_search
            USING fts5(
                filepath UNINDEXED,
                content,
                content_lower,
                tokenize='porter unicode61'
            )
        """)
        
        await self.db.commit()
        
    async def close(self):
        """Close database connection."""
        if self.db:
            await self.db.close()
            self.db = None
            
    async def get_file_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Get cached file information."""
        async with self._lock:
            cursor = await self.db.execute(
                "SELECT mtime, size, content_hash, last_indexed FROM file_index WHERE filepath = ?",
                (filepath,)
            )
            row = await cursor.fetchone()
            
            if row:
                return {
                    "mtime": row[0],
                    "size": row[1],
                    "content_hash": row[2],
                    "last_indexed": row[3]
                }
            return None
            
    async def needs_update(self, filepath: str, current_mtime: float, current_size: int) -> bool:
        """Check if a file needs to be re-indexed."""
        file_info = await self.get_file_info(filepath)
        
        if not file_info:
            return True
            
        # Check if file has been modified
        if file_info["mtime"] != current_mtime or file_info["size"] != current_size:
            return True
            
        return False
        
    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
        
    def _determine_property_type(self, value: Any) -> str:
        """Determine the type of a property value."""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'number'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, list):
            return 'list'
        elif isinstance(value, dict):
            return 'object'
        elif isinstance(value, str):
            # Check if it's a date-like string
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return 'date'
            except:
                return 'text'
        else:
            return 'text'
    
    def _calculate_line_offsets(self, content: str) -> List[int]:
        """Calculate byte offsets of each line start."""
        line_offsets = [0]
        for i, char in enumerate(content):
            if char == '\n':
                line_offsets.append(i + 1)
        return line_offsets
        
    async def index_file(self, filepath: str, content: str, mtime: float, size: int, metadata: Optional[Dict] = None):
        """Index a single file with its content and properties."""
        content_hash = self._compute_hash(content)
        content_lower = content.lower()
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Calculate line offsets for efficient line number lookups
        line_offsets = self._calculate_line_offsets(content)
        line_offsets_json = json.dumps(line_offsets)
        
        now = datetime.now().timestamp()
        
        async with self._lock:
            # Update main index
            await self.db.execute("""
                INSERT OR REPLACE INTO file_index 
                (filepath, content, content_lower, mtime, size, content_hash, last_indexed, metadata, line_offsets)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (filepath, content, content_lower, mtime, size, content_hash, now, metadata_json, line_offsets_json))
            
            # Update FTS index
            await self.db.execute(
                "DELETE FROM file_search WHERE filepath = ?",
                (filepath,)
            )
            await self.db.execute(
                "INSERT INTO file_search (filepath, content, content_lower) VALUES (?, ?, ?)",
                (filepath, content, content_lower)
            )
            
            # Update properties if metadata contains frontmatter
            if metadata and 'frontmatter' in metadata:
                # Clear existing properties for this file
                await self.db.execute(
                    "DELETE FROM file_properties WHERE filepath = ?",
                    (filepath,)
                )
                
                # Insert new properties
                frontmatter = metadata['frontmatter']
                for prop_name, prop_value in frontmatter.items():
                    # Determine property type
                    prop_type = self._determine_property_type(prop_value)
                    
                    # Convert value to string for storage
                    if isinstance(prop_value, (list, dict)):
                        prop_value_str = json.dumps(prop_value)
                    else:
                        prop_value_str = str(prop_value)
                    
                    await self.db.execute("""
                        INSERT INTO file_properties (filepath, property_name, property_value, property_type)
                        VALUES (?, ?, ?, ?)
                    """, (filepath, prop_name, prop_value_str, prop_type))
            
            await self.db.commit()
            
    async def remove_file(self, filepath: str):
        """Remove a file from the index."""
        async with self._lock:
            await self.db.execute("DELETE FROM file_index WHERE filepath = ?", (filepath,))
            await self.db.execute("DELETE FROM file_search WHERE filepath = ?", (filepath,))
            await self.db.commit()
            
    async def search_content(self, query: str, limit: int = 50) -> List[Tuple[str, str]]:
        """
        Search for content using FTS5.
        
        Returns list of (filepath, snippet) tuples.
        """
        # Use FTS5 for efficient full-text search
        cursor = await self.db.execute("""
            SELECT filepath, snippet(file_search, 1, '<b>', '</b>', '...', 32)
            FROM file_search
            WHERE file_search MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        results = await cursor.fetchall()
        return results
        
    async def search_simple(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Simple substring search (for compatibility with current implementation).
        
        Returns list of file info dictionaries.
        """
        query_lower = query.lower()
        cursor = await self.db.execute("""
            SELECT filepath, content, mtime, size
            FROM file_index
            WHERE content_lower LIKE ?
            LIMIT ?
        """, (f"%{query_lower}%", limit))
        
        results = []
        async for row in cursor:
            results.append({
                "filepath": row[0],
                "content": row[1],
                "mtime": row[2],
                "size": row[3]
            })
            
        return results
        
    async def search_regex(self, pattern: str, flags: int = 0, limit: int = 50, 
                          context_length: int = 100, max_parallel: int = 10) -> List[Dict[str, Any]]:
        """
        Search using regular expressions with efficient streaming and parallel processing.
        
        Args:
            pattern: Regular expression pattern
            flags: Regex flags (e.g., re.IGNORECASE)
            limit: Maximum number of results
            context_length: Characters to show around match
            max_parallel: Maximum number of files to process in parallel
            
        Returns:
            List of search results with matches and context
        """
        import re
        
        # Compile regex pattern
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        
        # Check if we can use FTS5 pre-filtering
        literal_prefix = self._extract_literal_prefix(pattern)
        
        # Build query - order by size for faster initial results
        if literal_prefix and len(literal_prefix) >= 3:
            # Escape special characters for FTS5
            # FTS5 requires double quotes around phrases with special characters
            fts5_query = f'"{literal_prefix}"'
            
            # Use FTS5 to pre-filter files containing the literal prefix
            query = """
                SELECT f.filepath, f.content, f.mtime, f.size, f.line_offsets
                FROM file_index f
                JOIN file_search s ON f.filepath = s.filepath
                WHERE file_search MATCH ?
                ORDER BY f.size ASC, f.mtime DESC
            """
            params = (fts5_query,)
        else:
            # Full scan, but ordered by size
            query = """
                SELECT filepath, content, mtime, size, line_offsets
                FROM file_index
                ORDER BY size ASC, mtime DESC
            """
            params = ()
        
        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        
        # Process files in batches for parallel execution
        results = []
        total_results = 0
        batch_size = max_parallel
        
        for i in range(0, len(rows), batch_size):
            if total_results >= limit:
                break
                
            batch = rows[i:i + batch_size]
            
            # Process batch in parallel
            batch_tasks = []
            for row in batch:
                if total_results >= limit:
                    break
                    
                filepath, content, mtime, size, line_offsets_json = row
                
                # Create task for processing this file
                task = self._process_file_regex(
                    filepath, content, size, line_offsets_json,
                    regex, context_length
                )
                batch_tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Collect results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error processing file: {result}")
                    continue
                    
                if result and result['match_contexts']:
                    results.append({
                        "filepath": result['filepath'],
                        "match_count": len(result['match_contexts']),
                        "matches": result['match_contexts'],
                        "score": min(len(result['match_contexts']) / 5.0 + 1.0, 5.0)
                    })
                    total_results += 1
                    
                    if total_results >= limit:
                        break
        
        return results[:limit]
    
    async def _process_file_regex(self, filepath: str, content: str, size: int,
                                 line_offsets_json: Optional[str], regex,
                                 context_length: int, max_matches: int = 5) -> Dict[str, Any]:
        """Process a single file for regex matches (for parallel execution)."""
        # Parse line offsets if available
        try:
            line_offsets = json.loads(line_offsets_json) if line_offsets_json else None
        except:
            line_offsets = None
        
        # For large files, use streaming approach
        if size > 1024 * 1024:  # 1MB threshold
            match_contexts = await self._search_large_file_streaming(
                content, regex, line_offsets, context_length, max_matches
            )
        else:
            # For smaller files, use the optimized standard approach
            match_contexts = self._search_file_content(
                content, regex, line_offsets, context_length, max_matches
            )
        
        return {
            'filepath': filepath,
            'match_contexts': match_contexts
        }
    
    def _extract_literal_prefix(self, pattern: str) -> Optional[str]:
        """Extract a literal prefix from regex pattern for FTS5 pre-filtering."""
        # Simple extraction - look for literal characters at the start
        literal = ""
        escaped = False
        
        for char in pattern:
            if escaped:
                # If it's a regex escape sequence, stop extraction
                if char in 'dDwWsSbBAZ':  # Common regex escape sequences
                    break
                elif char in 'nrtfv':  # Special character escapes
                    break
                elif char in '.^$*+?{[|(\\':  # Escaped metacharacters
                    literal += char
                else:
                    # Unknown escape, stop extraction to be safe
                    break
                escaped = False
            elif char == '\\':
                escaped = True
            elif char in '.^$*+?{[|(':
                break  # Regex metacharacter
            else:
                literal += char
        
        return literal if len(literal) >= 3 else None
    
    def _search_file_content(self, content: str, regex, line_offsets: Optional[List[int]], 
                           context_length: int, max_matches: int = 5) -> List[Dict[str, Any]]:
        """Search content and return match contexts."""
        match_contexts = []
        match_count = 0
        
        # Use finditer for streaming matches
        for match in regex.finditer(content):
            if match_count >= max_matches:
                break
                
            match_start = match.start()
            match_end = match.end()
            
            # Find line number efficiently
            if line_offsets:
                line_num = self._find_line_number(line_offsets, match_start)
            else:
                # Fallback: count newlines before match
                line_num = content[:match_start].count('\n') + 1
            
            # Extract context
            context_start = max(0, match_start - context_length // 2)
            context_end = min(len(content), match_end + context_length // 2)
            context = content[context_start:context_end].strip()
            
            # Add ellipsis if truncated
            if context_start > 0:
                context = "..." + context
            if context_end < len(content):
                context = context + "..."
            
            match_contexts.append({
                "match": match.group(0),
                "line": line_num,
                "context": context,
                "groups": match.groups() if match.groups() else None
            })
            
            match_count += 1
        
        return match_contexts
    
    async def _search_large_file_streaming(self, content: str, regex, line_offsets: Optional[List[int]], 
                                         context_length: int, max_matches: int = 5) -> List[Dict[str, Any]]:
        """Search large files using a streaming approach with chunks."""
        match_contexts = []
        chunk_size = 512 * 1024  # 512KB chunks
        overlap = 1024  # 1KB overlap to catch matches at boundaries
        
        pos = 0
        while pos < len(content) and len(match_contexts) < max_matches:
            # Extract chunk with overlap
            chunk_start = max(0, pos - overlap)
            chunk_end = min(len(content), pos + chunk_size)
            chunk = content[chunk_start:chunk_end]
            
            # Find matches in chunk
            for match in regex.finditer(chunk):
                # Adjust match position to full content coordinates
                match_start = chunk_start + match.start()
                match_end = chunk_start + match.end()
                
                # Skip if this match was already found in overlap
                if match_contexts and match_start <= match_contexts[-1]["match_start"]:
                    continue
                
                # Find line number
                if line_offsets:
                    line_num = self._find_line_number(line_offsets, match_start)
                else:
                    line_num = content[:match_start].count('\n') + 1
                
                # Extract context from full content
                context_start = max(0, match_start - context_length // 2)
                context_end = min(len(content), match_end + context_length // 2)
                context = content[context_start:context_end].strip()
                
                # Add ellipsis if truncated
                if context_start > 0:
                    context = "..." + context
                if context_end < len(content):
                    context = context + "..."
                
                match_contexts.append({
                    "match": match.group(0),
                    "line": line_num,
                    "context": context,
                    "groups": match.groups() if match.groups() else None,
                    "match_start": match_start  # For duplicate detection
                })
                
                if len(match_contexts) >= max_matches:
                    break
            
            # Move to next chunk
            pos += chunk_size
        
        # Remove the match_start field used for duplicate detection
        for match_ctx in match_contexts:
            match_ctx.pop("match_start", None)
        
        return match_contexts
    
    def _find_line_number(self, line_starts: List[int], position: int) -> int:
        """Find line number using binary search."""
        left, right = 0, len(line_starts) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if mid + 1 < len(line_starts):
                if line_starts[mid] <= position < line_starts[mid + 1]:
                    return mid + 1
                elif position < line_starts[mid]:
                    right = mid - 1
                else:
                    left = mid + 1
            else:
                return mid + 1
        
        return len(line_starts)
        
    async def get_all_files(self) -> List[str]:
        """Get list of all indexed files."""
        cursor = await self.db.execute("SELECT filepath FROM file_index")
        files = [row[0] for row in await cursor.fetchall()]
        return files
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        cursor = await self.db.execute("SELECT COUNT(*), SUM(size), MAX(last_indexed) FROM file_index")
        row = await cursor.fetchone()
        
        return {
            "total_files": row[0] or 0,
            "total_size": row[1] or 0,
            "last_update": datetime.fromtimestamp(row[2]) if row[2] else None
        }
        
    async def clear_orphaned_entries(self, existing_files: set):
        """Remove index entries for files that no longer exist."""
        async with self._lock:
            cursor = await self.db.execute("SELECT filepath FROM file_index")
            indexed_files = {row[0] for row in await cursor.fetchall()}
            
            orphaned = indexed_files - existing_files
            
            for filepath in orphaned:
                await self.remove_file(filepath)
                logger.info(f"Removed orphaned index entry: {filepath}")
                
    async def search_by_property(self, property_name: str, operator: str, value: Optional[str] = None, 
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for files by property values.
        
        Args:
            property_name: Name of the property to search
            operator: Comparison operator (=, !=, >, <, >=, <=, contains, exists)
            value: Value to compare against (optional for 'exists')
            limit: Maximum number of results
            
        Returns:
            List of file info with matching properties
        """
        # Build SQL query based on operator
        if operator == 'exists':
            sql = """
                SELECT DISTINCT f.filepath, f.content, p.property_value, p.property_type
                FROM file_index f
                JOIN file_properties p ON f.filepath = p.filepath
                WHERE p.property_name = ?
                ORDER BY f.mtime DESC
                LIMIT ?
            """
            params = (property_name, limit)
            
        elif operator == 'contains':
            sql = """
                SELECT DISTINCT f.filepath, f.content, p.property_value, p.property_type
                FROM file_index f
                JOIN file_properties p ON f.filepath = p.filepath
                WHERE p.property_name = ? AND p.property_value LIKE ?
                ORDER BY f.mtime DESC
                LIMIT ?
            """
            params = (property_name, f"%{value}%", limit)
            
        elif operator == '!=':
            # For not equal, we need to include files without the property
            sql = """
                SELECT DISTINCT f.filepath, f.content, 
                       COALESCE(p.property_value, '') as property_value,
                       COALESCE(p.property_type, '') as property_type
                FROM file_index f
                LEFT JOIN file_properties p ON f.filepath = p.filepath AND p.property_name = ?
                WHERE p.property_value IS NULL OR p.property_value != ?
                ORDER BY f.mtime DESC
                LIMIT ?
            """
            params = (property_name, value, limit)
            
        else:  # =, >, <, >=, <=
            # For numeric comparisons, we need to handle type conversion
            if operator in ['>', '<', '>=', '<=']:
                sql = f"""
                    SELECT DISTINCT f.filepath, f.content, p.property_value, p.property_type
                    FROM file_index f
                    JOIN file_properties p ON f.filepath = p.filepath
                    WHERE p.property_name = ? AND 
                          ((p.property_type = 'number' AND CAST(p.property_value AS REAL) {operator} CAST(? AS REAL)) OR
                           (p.property_type != 'number' AND p.property_value {operator} ?))
                    ORDER BY f.mtime DESC
                    LIMIT ?
                """
                params = (property_name, value, value, limit)
            else:  # = operator
                sql = """
                    SELECT DISTINCT f.filepath, f.content, p.property_value, p.property_type
                    FROM file_index f
                    JOIN file_properties p ON f.filepath = p.filepath
                    WHERE p.property_name = ? AND LOWER(p.property_value) = LOWER(?)
                    ORDER BY f.mtime DESC
                    LIMIT ?
                """
                params = (property_name, value, limit)
        
        cursor = await self.db.execute(sql, params)
        
        results = []
        async for row in cursor:
            results.append({
                "filepath": row[0],
                "content": row[1],
                "property_value": row[2],
                "property_type": row[3] if len(row) > 3 else None
            })
            
        return results
        
    async def get_all_property_names(self) -> List[str]:
        """Get a list of all unique property names in the index."""
        cursor = await self.db.execute("""
            SELECT DISTINCT property_name 
            FROM file_properties 
            ORDER BY property_name
        """)
        
        return [row[0] for row in await cursor.fetchall()]
        
    async def get_property_values(self, property_name: str) -> List[Tuple[str, int]]:
        """Get all unique values for a property with counts."""
        cursor = await self.db.execute("""
            SELECT property_value, COUNT(*) as count
            FROM file_properties
            WHERE property_name = ?
            GROUP BY property_value
            ORDER BY count DESC, property_value
        """, (property_name,))
        
        return await cursor.fetchall()