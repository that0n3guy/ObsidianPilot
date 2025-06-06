"""Unit tests for Obsidian MCP server.

Combines all unit tests into a single file for simplicity.
Run with: pytest tests/test_unit.py -v
Or without pytest: python tests/run_tests.py unit
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.tools.note_management import read_note, create_note, update_note, delete_note
from src.tools.search_discovery import search_notes, list_notes
from src.tools.organization import move_note, add_tags, remove_tags, get_note_info, _update_frontmatter_tags
from src.models import Note, NoteMetadata, VaultItem


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
        vault_items = [
            VaultItem(path="test", name="test", is_folder=True, children=[
                VaultItem(path="test/note.md", name="note.md", is_folder=False)
            ])
        ]
        
        with patch('src.tools.search_discovery.ObsidianAPI') as mock_api_class:
            mock_api = mock_api_class.return_value
            mock_api.get_vault_structure = AsyncMock(return_value=vault_items)
            
            result = await list_notes(recursive=True, ctx=mock_ctx)
            
            assert result["count"] >= 1


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