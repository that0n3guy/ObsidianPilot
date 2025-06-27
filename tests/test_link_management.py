"""Tests for link management functionality."""

import pytest
from obsidianpilot.tools.link_management import (
    extract_links_from_content,
    get_link_context,
    get_backlinks,
    get_outgoing_links,
    find_broken_links
)


class TestLinkExtraction:
    """Test link extraction from content."""
    
    def test_extract_wiki_links(self):
        """Test extracting wiki-style links."""
        content = """
        Here's a link to [[Daily Note]].
        And another to [[Projects/AI Research]].
        With alias: [[Long Note Name|Short Name]].
        With header: [[Note#Section]].
        Complex: [[Projects/Note#Header|Custom Text]].
        """
        
        links = extract_links_from_content(content)
        
        assert len(links) == 5
        assert links[0] == {
            'path': 'Daily Note.md',
            'display_text': 'Daily Note',
            'type': 'wiki'
        }
        assert links[1] == {
            'path': 'Projects/AI Research.md',
            'display_text': 'Projects/AI Research',
            'type': 'wiki'
        }
        assert links[2] == {
            'path': 'Long Note Name.md',
            'display_text': 'Short Name',
            'type': 'wiki'
        }
        assert links[3] == {
            'path': 'Note.md',
            'display_text': 'Note',
            'type': 'wiki',
            'header': 'Section'
        }
    
    def test_extract_markdown_links(self):
        """Test extracting markdown-style links."""
        content = """
        Here's a [markdown link](note.md).
        And [another one](folder/note.md).
        External: [Google](https://google.com) should be ignored.
        """
        
        links = extract_links_from_content(content)
        
        assert len(links) == 2
        assert links[0] == {
            'path': 'note.md',
            'display_text': 'markdown link',
            'type': 'markdown'
        }
        assert links[1] == {
            'path': 'folder/note.md',
            'display_text': 'another one',
            'type': 'markdown'
        }
    
    def test_mixed_link_types(self):
        """Test extracting both wiki and markdown links."""
        content = """
        Wiki link: [[Projects/Overview]]
        Markdown link: [Overview](projects/overview.md)
        """
        
        links = extract_links_from_content(content)
        
        assert len(links) == 2
        assert links[0]['type'] == 'wiki'
        assert links[1]['type'] == 'markdown'


class TestLinkContext:
    """Test context extraction around links."""
    
    def test_get_link_context(self):
        """Test extracting context around a link."""
        import re
        
        content = "This is some text before the [[Important Link]] and some text after it."
        pattern = re.compile(r'\[\[([^\]]+)\]\]')
        match = pattern.search(content)
        
        context = get_link_context(content, match, context_length=30)
        
        assert "before the [[Important Link]] and some" in context
    
    def test_context_at_boundaries(self):
        """Test context extraction at content boundaries."""
        import re
        
        content = "[[Link]] at start"
        pattern = re.compile(r'\[\[([^\]]+)\]\]')
        match = pattern.search(content)
        
        context = get_link_context(content, match, context_length=50)
        
        assert context == "[[Link]] at start"
        assert not context.startswith("...")


class TestBacklinksIntegration:
    """Integration tests for backlinks functionality."""
    
    @pytest.mark.asyncio
    async def test_get_backlinks_structure(self):
        """Test the structure of backlinks response."""
        # This test requires a mock or actual Obsidian API
        # For now, we'll test the function exists and can be called
        # In a real test environment, you'd mock the ObsidianAPI
        pass
    
    @pytest.mark.asyncio
    async def test_get_outgoing_links_structure(self):
        """Test the structure of outgoing links response."""
        # This test requires a mock or actual Obsidian API
        pass
    
    @pytest.mark.asyncio
    async def test_find_broken_links_structure(self):
        """Test the structure of broken links response."""
        # This test requires a mock or actual Obsidian API
        pass


class TestLinkValidation:
    """Test link validation functionality."""
    
    def test_normalize_paths(self):
        """Test that paths are normalized correctly."""
        content = "[[Note]] and [[Note.md]] should be treated the same"
        links = extract_links_from_content(content)
        
        assert len(links) == 2
        assert links[0]['path'] == 'Note.md'
        assert links[1]['path'] == 'Note.md'
    
    def test_preserve_folder_structure(self):
        """Test that folder paths are preserved."""
        content = "[[Projects/Subfolder/Deep Note]]"
        links = extract_links_from_content(content)
        
        assert links[0]['path'] == 'Projects/Subfolder/Deep Note.md'


if __name__ == "__main__":
    # Run basic tests
    test = TestLinkExtraction()
    test.test_extract_wiki_links()
    test.test_extract_markdown_links()
    test.test_mixed_link_types()
    
    test2 = TestLinkContext()
    test2.test_get_link_context()
    test2.test_context_at_boundaries()
    
    test3 = TestLinkValidation()
    test3.test_normalize_paths()
    test3.test_preserve_folder_structure()
    
    print("All basic tests passed!")