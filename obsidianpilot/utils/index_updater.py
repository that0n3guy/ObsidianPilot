"""Automatic index updating for file changes."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Set, Dict, Any
from .fts_search import get_fts_search
from .filesystem import get_vault

logger = logging.getLogger(__name__)


class IndexUpdater:
    """Tracks file changes and updates the search index automatically."""
    
    def __init__(self, check_interval: int = 10):
        """
        Initialize the index updater.
        
        Args:
            check_interval: How often to check for changes (seconds)
        """
        self.check_interval = check_interval
        self._last_check = 0
        self._file_mtimes: Dict[str, float] = {}
        self._running = False
        
    async def check_and_update(self) -> Dict[str, Any]:
        """Check for file changes and update index."""
        vault = get_vault()
        fts = await get_fts_search()
        
        # Get current files
        all_notes = await vault.list_notes(recursive=True)
        current_files = {note['path'] for note in all_notes}
        
        # Get indexed files
        stats = await fts.get_stats()
        if stats['total_files'] == 0:
            return {"status": "no_index", "message": "Index not built yet"}
        
        # Track changes
        added_files = []
        modified_files = []
        deleted_files = []
        
        # Check each file (skip .trash folder)
        for note_info in all_notes:
            filepath = note_info['path']
            
            # Skip files in .trash and .obsidian folders (handle both Windows \ and Unix / separators)
            filepath_normalized = filepath.replace('\\', '/')
            if (filepath_normalized.startswith('.trash/') or '/.trash/' in filepath_normalized or
                filepath_normalized.startswith('.obsidian/') or '/.obsidian/' in filepath_normalized):
                continue
                
            full_path = vault.vault_path / filepath
            
            try:
                mtime = full_path.stat().st_mtime
                
                # Check if file is new or modified
                if filepath not in self._file_mtimes:
                    added_files.append(filepath)
                elif mtime > self._file_mtimes[filepath]:
                    modified_files.append(filepath)
                    
                self._file_mtimes[filepath] = mtime
                
            except Exception as e:
                logger.warning(f"Failed to check file {filepath}: {e}")
        
        # Check for deleted files
        for filepath in list(self._file_mtimes.keys()):
            if filepath not in current_files:
                deleted_files.append(filepath)
                del self._file_mtimes[filepath]
        
        # Update index for changes
        updated_count = 0
        
        # Handle additions and modifications
        for filepath in added_files + modified_files:
            try:
                note = await vault.read_note(filepath)
                await fts.index_file(note.path, note.content, note.metadata)
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to index {filepath}: {e}")
        
        # Handle deletions
        for filepath in deleted_files:
            try:
                await fts.remove_file(filepath)
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove {filepath} from index: {e}")
        
        return {
            "status": "updated",
            "added": len(added_files),
            "modified": len(modified_files),
            "deleted": len(deleted_files),
            "total_updated": updated_count,
            "total_files": len(current_files)
        }
    
    async def start_auto_update(self):
        """Start automatic index updates in the background."""
        if self._running:
            return
            
        self._running = True
        logger.info("Starting automatic index updates")
        
        while self._running:
            try:
                # Check if enough time has passed
                current_time = time.time()
                if current_time - self._last_check >= self.check_interval:
                    result = await self.check_and_update()
                    self._last_check = current_time
                    
                    if result['status'] == 'updated' and result['total_updated'] > 0:
                        logger.info(f"Index updated: {result['added']} added, "
                                  f"{result['modified']} modified, {result['deleted']} deleted")
                
                # Sleep for a bit before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in auto-update: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def stop(self):
        """Stop automatic updates."""
        self._running = False


# Global updater instance
_index_updater = None


async def start_index_updater():
    """Start the global index updater."""
    global _index_updater
    
    if _index_updater is None:
        _index_updater = IndexUpdater()
        asyncio.create_task(_index_updater.start_auto_update())
        logger.info("Index updater started")


async def update_index_for_file(filepath: str):
    """Update index for a specific file (called after create/update operations)."""
    try:
        # Skip files in .trash and .obsidian folders (handle both Windows \ and Unix / separators)
        filepath_normalized = filepath.replace('\\', '/')
        if (filepath_normalized.startswith('.trash/') or '/.trash/' in filepath_normalized or
            filepath_normalized.startswith('.obsidian/') or '/.obsidian/' in filepath_normalized):
            logger.debug(f"Skipping index update for excluded file: {filepath}")
            return
        
        vault = get_vault()
        fts = await get_fts_search()
        
        # Check if index exists
        stats = await fts.get_stats()
        if stats['total_files'] == 0:
            return  # No index yet
        
        # Update the file in index
        note = await vault.read_note(filepath)
        await fts.index_file(note.path, note.content, note.metadata)
        logger.debug(f"Updated index for {filepath}")
        
    except Exception as e:
        logger.warning(f"Failed to update index for {filepath}: {e}")