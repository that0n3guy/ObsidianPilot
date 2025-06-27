"""Unit tests for Obsidian MCP server.

Combines all unit tests into a single file for simplicity.
Run with: pytest tests/test_unit.py -v
Or without pytest: python tests/run_tests.py unit
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from obsidianpilot.tools.note_management import read_note, create_note, update_note, delete_note
from obsidianpilot.tools.search_discovery import search_notes, list_notes
from obsidianpilot.tools.organization import move_note, add_tags, remove_tags, get_note_info, _update_frontmatter_tags
from obsidianpilot.models import Note, NoteMetadata, VaultItem


@pytest.fixture
def mock_ctx():
    """Mock FastMCP context."""
    ctx = Mock()
    ctx.info = Mock()
    return ctx


@pytest.fixture
def sample_note():
    """Sample note for testing."""
    return Note(
        path="test/sample.md",
        content="# Test Note\n\nThis is a test note.",
        metadata=NoteMetadata(tags=["test", "sample"])
    )


class TestNoteManagement:
    """Tests for note CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_read_note_success(self, mock_ctx, sample_note):
        """Test successful note reading."""
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=sample_note)
            
            result = await read_note("test/sample.md", mock_ctx)
            
            assert result["path"] == "test/sample.md"
            assert "Test Note" in result["content"]
            assert result["metadata"]["tags"] == ["test", "sample"]
    
    @pytest.mark.asyncio
    async def test_read_note_not_found(self, mock_ctx):
        """Test reading non-existent note."""
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=None)
            
            with pytest.raises(FileNotFoundError):
                await read_note("nonexistent.md", mock_ctx)
    
    @pytest.mark.asyncio
    async def test_create_note_success(self, mock_ctx, sample_note):
        """Test successful note creation."""
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=None)
            mock_api.create_note = AsyncMock(return_value=sample_note)
            
            result = await create_note("test/new.md", "# New Note", ctx=mock_ctx)
            
            assert result["created"] is True
            assert result["path"] == "test/sample.md"
    
    @pytest.mark.asyncio
    async def test_update_note_success(self, mock_ctx, sample_note):
        """Test successful note update."""
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=sample_note)
            mock_api.update_note = AsyncMock(return_value=sample_note)
            
            result = await update_note("test/sample.md", "# Updated", ctx=mock_ctx)
            
            assert result["updated"] is True
            assert result["created"] is False
    
    @pytest.mark.asyncio
    async def test_update_note_append_strategy(self, mock_ctx, sample_note):
        """Test update note with append merge strategy."""
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=sample_note)
            
            # Create a new note with appended content
            expected_content = sample_note.content.rstrip() + "\n\n## Additional Content"
            updated_note = Note(
                path=sample_note.path,
                content=expected_content,
                metadata=sample_note.metadata
            )
            mock_api.update_note = AsyncMock(return_value=updated_note)
            
            result = await update_note(
                "test/sample.md", 
                "## Additional Content", 
                merge_strategy="append",
                ctx=mock_ctx
            )
            
            assert result["updated"] is True
            assert result["created"] is False
            assert result["merge_strategy"] == "append"
            
            # Verify the API was called with the appended content
            mock_api.update_note.assert_called_once_with(
                "test/sample.md", 
                expected_content
            )
    
    @pytest.mark.asyncio
    async def test_update_note_replace_strategy(self, mock_ctx, sample_note):
        """Test update note with explicit replace merge strategy."""
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=sample_note)
            
            new_content = "# Completely New Content"
            updated_note = Note(
                path=sample_note.path,
                content=new_content,
                metadata=sample_note.metadata
            )
            mock_api.update_note = AsyncMock(return_value=updated_note)
            
            result = await update_note(
                "test/sample.md", 
                new_content,
                merge_strategy="replace",
                ctx=mock_ctx
            )
            
            assert result["updated"] is True
            assert result["created"] is False
            assert result["merge_strategy"] == "replace"
            
            # Verify the API was called with the replaced content
            mock_api.update_note.assert_called_once_with(
                "test/sample.md", 
                new_content
            )
    
    @pytest.mark.asyncio
    async def test_update_note_invalid_strategy(self, mock_ctx, sample_note):
        """Test update note with invalid merge strategy."""
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=sample_note)
            
            with pytest.raises(ValueError) as exc_info:
                await update_note(
                    "test/sample.md", 
                    "# Content",
                    merge_strategy="invalid",
                    ctx=mock_ctx
                )
            
            assert "Invalid merge_strategy" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_note_success(self, mock_ctx):
        """Test successful note deletion."""
        with patch('src.tools.note_management.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.delete_note = AsyncMock(return_value=True)
            
            result = await delete_note("test/sample.md", mock_ctx)
            
            assert result["deleted"] is True


class TestSearchDiscovery:
    """Tests for search and list operations."""
    
    @pytest.mark.asyncio
    async def test_search_notes(self, mock_ctx):
        """Test note searching."""
        mock_results = [{
            "path": "test.md",
            "content": "Test content",
            "score": 0.9,
            "matches": [{"match": "test", "start": 0, "end": 4}]
        }]
        
        with patch('src.tools.search_discovery.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.search = AsyncMock(return_value=mock_results)
            
            result = await search_notes("test", ctx=mock_ctx)
            
            assert result["count"] == 1
            assert result["query"] == "test"
    
    @pytest.mark.asyncio
    async def test_list_notes(self, mock_ctx):
        """Test listing notes."""
        # For simplicity, test non-recursive listing of a specific directory
        folder_items = [
            VaultItem(path="note1.md", name="note1.md", is_folder=False, children=None),
            VaultItem(path="subfolder", name="subfolder", is_folder=True, children=None),
            VaultItem(path="note2.md", name="note2.md", is_folder=False, children=None)
        ]
        
        with patch('src.tools.search_discovery.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_vault_structure = AsyncMock(return_value=folder_items)
            
            # Test non-recursive listing
            result = await list_notes(directory="test", recursive=False, ctx=mock_ctx)
            
            # Should only find the markdown files, not recurse into subfolder
            assert result["count"] == 2
            assert result["directory"] == "test"
            assert result["notes"][0]["path"] == "test/note1.md"
            assert result["notes"][1]["path"] == "test/note2.md"


class TestOrganization:
    """Tests for organization tools."""
    
    @pytest.mark.asyncio
    async def test_add_tags(self, mock_ctx, sample_note):
        """Test adding tags."""
        updated_note = Note(
            path=sample_note.path,
            content=sample_note.content,
            metadata=NoteMetadata(tags=["test", "sample", "new"])
        )
        
        with patch('src.tools.organization.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(side_effect=[sample_note, updated_note])
            mock_api.update_note = AsyncMock()
            
            result = await add_tags("test/sample.md", ["new"], ctx=mock_ctx)
            
            assert "new" in result["tags_added"]
    
    @pytest.mark.asyncio
    async def test_get_note_info(self, mock_ctx, sample_note):
        """Test getting note info."""
        with patch('src.tools.organization.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_note = AsyncMock(return_value=sample_note)
            
            result = await get_note_info("test/sample.md", ctx=mock_ctx)
            
            assert result["exists"] is True
            assert result["stats"]["word_count"] > 0
    
    def test_update_frontmatter_tags(self):
        """Test frontmatter tag updates."""
        content = "---\ntags: [existing]\n---\n\nContent"
        result = _update_frontmatter_tags(content, ["new"], "add")
        assert "tags: [existing, new]" in result