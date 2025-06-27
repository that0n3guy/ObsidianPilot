"""Integration tests for Obsidian MCP server.

Tests the integration between tools and models without requiring Obsidian.
Run with: pytest tests/test_integration.py -v
"""

import pytest
from unittest.mock import patch, AsyncMock
from obsidianpilot.tools import (
    read_note, create_note, update_note, delete_note,
    search_notes, list_notes, move_note, add_tags, get_note_info
)
from obsidianpilot.models import Note, NoteMetadata, VaultItem


class MockContext:
    """Mock context for testing."""
    def info(self, msg):
        pass


class TestToolIntegration:
    """Test tool integration with models and error handling."""
    
    @pytest.mark.asyncio
    async def test_note_creation_flow(self):
        """Test complete note creation and reading flow."""
        ctx = MockContext()
        
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            
            # Mock successful creation
            created_note = Note(
                path="test/new.md",
                content="# New Note",
                metadata=NoteMetadata()
            )
            mock_api.get_note = AsyncMock(side_effect=[None, created_note])
            mock_api.create_note = AsyncMock(return_value=created_note)
            
            # Create note
            result = await create_note("test/new.md", "# New Note", ctx=ctx)
            assert result["created"] is True
            assert result["path"] == "test/new.md"
            
            # Verify it can be read
            mock_api.get_note = AsyncMock(return_value=created_note)
            read_result = await read_note("test/new.md", ctx)
            assert read_result["content"] == "# New Note"
    
    @pytest.mark.asyncio
    async def test_search_integration(self):
        """Test search with result processing."""
        ctx = MockContext()
        
        with patch('src.tools.search_discovery.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.search = AsyncMock(return_value=[
                {
                    "path": "notes/test.md",
                    "content": "This is a test note with search term",
                    "score": 0.95,
                    "matches": [{"match": "test", "start": 10, "end": 14}]
                }
            ])
            
            result = await search_notes("test", context_length=50, ctx=ctx)
            
            assert result["count"] == 1
            assert result["results"][0]["path"] == "notes/test.md"
            # matches is a list of dicts, check if any match contains "test"
            assert any(m["match"] == "test" for m in result["results"][0]["matches"])
    
    @pytest.mark.asyncio
    async def test_list_notes_integration(self):
        """Test listing notes with vault structure parsing."""
        ctx = MockContext()
        
        with patch('src.tools.search_discovery.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            
            # Mock vault structure
            vault_items = [
                VaultItem(path="Projects", name="Projects", is_folder=True),
                VaultItem(path="Projects/AI.md", name="AI.md", is_folder=False),
                VaultItem(path="Daily", name="Daily", is_folder=True),
                VaultItem(path="README.md", name="README.md", is_folder=False)
            ]
            mock_api.get_vault_structure = AsyncMock(return_value=vault_items)
            
            result = await list_notes(recursive=True, ctx=ctx)
            
            assert result["count"] >= 1
            assert any(n["path"] == "README.md" for n in result["notes"])
    
    @pytest.mark.asyncio
    async def test_tag_operations_integration(self):
        """Test tag add/remove flow."""
        ctx = MockContext()
        
        with patch('src.tools.organization.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            
            # Initial note with tags
            note = Note(
                path="test/tagged.md",
                content="---\ntags: [existing]\n---\n\nContent",
                metadata=NoteMetadata(tags=["existing"])
            )
            
            # Mock the flow
            mock_api.get_note = AsyncMock(return_value=note)
            mock_api.update_note = AsyncMock()
            
            # Add tags
            add_result = await add_tags("test/tagged.md", ["new", "test"], ctx)
            assert "new" in add_result["tags_added"]
            
            # The update should have been called
            mock_api.update_note.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_note_merge_strategies(self):
        """Test update note with different merge strategies."""
        ctx = MockContext()
        
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            
            # Existing note
            existing_note = Note(
                path="test/note.md",
                content="# Original Content\n\nOriginal text here.",
                metadata=NoteMetadata()
            )
            
            # Test append strategy
            mock_api.get_note = AsyncMock(return_value=existing_note)
            expected_appended = existing_note.content.rstrip() + "\n\n## New Section\n\nAdditional content."
            appended_note = Note(
                path=existing_note.path,
                content=expected_appended,
                metadata=existing_note.metadata
            )
            mock_api.update_note = AsyncMock(return_value=appended_note)
            
            result = await update_note(
                "test/note.md",
                "## New Section\n\nAdditional content.",
                merge_strategy="append",
                ctx=ctx
            )
            
            assert result["updated"] is True
            assert result["merge_strategy"] == "append"
            mock_api.update_note.assert_called_with("test/note.md", expected_appended)
            
            # Test replace strategy (default)
            mock_api.get_note = AsyncMock(return_value=existing_note)
            new_content = "# Completely New Content\n\nReplaced everything."
            replaced_note = Note(
                path=existing_note.path,
                content=new_content,
                metadata=existing_note.metadata
            )
            mock_api.update_note = AsyncMock(return_value=replaced_note)
            
            result = await update_note(
                "test/note.md",
                new_content,
                ctx=ctx
            )
            
            assert result["updated"] is True
            assert result["merge_strategy"] == "replace"
            mock_api.update_note.assert_called_with("test/note.md", new_content)
    
    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test that errors are properly propagated."""
        ctx = MockContext()
        
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=None)
            
            # Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                await read_note("nonexistent.md", ctx)
    
    @pytest.mark.asyncio
    async def test_move_note_integration(self):
        """Test moving a note."""
        ctx = MockContext()
        
        with patch('src.tools.organization.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            
            # Source note exists
            source_note = Note(
                path="old/path.md",
                content="# Content",
                metadata=NoteMetadata()
            )
            
            mock_api.get_note = AsyncMock(side_effect=[source_note, None])
            mock_api.create_note = AsyncMock()
            mock_api.delete_note = AsyncMock(return_value=True)
            
            result = await move_note("old/path.md", "new/path.md", ctx=ctx)
            
            assert result["moved"] is True
            assert result["source"] == "old/path.md"
            assert result["destination"] == "new/path.md"
            
            # Verify create and delete were called
            mock_api.create_note.assert_called_once()
            mock_api.delete_note.assert_called_once()


class TestModelValidation:
    """Test model validation and edge cases."""
    
    def test_note_path_validation(self):
        """Test Note model path validation."""
        # Valid note
        note = Note(
            path="valid/path.md",
            content="Content",
            metadata=NoteMetadata()
        )
        assert note.path == "valid/path.md"
        
        # Invalid path with ..
        with pytest.raises(ValueError):
            Note(
                path="../etc/passwd",
                content="Content",
                metadata=NoteMetadata()
            )
    
    def test_tag_validation(self):
        """Test tag name cleaning."""
        from obsidianpilot.models import Tag
        
        tag = Tag(name="#test", count=5)
        assert tag.name == "test"  # # should be removed
    
    def test_vault_item_hierarchy(self):
        """Test VaultItem with children."""
        folder = VaultItem(
            path="Projects",
            name="Projects",
            is_folder=True,
            children=[
                VaultItem(path="Projects/AI.md", name="AI.md", is_folder=False)
            ]
        )
        
        assert folder.is_folder
        assert len(folder.children) == 1
        assert folder.children[0].name == "AI.md"