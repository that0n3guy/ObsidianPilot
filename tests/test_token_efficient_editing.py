"""Tests for token-efficient editing tools."""

import pytest
import tempfile
import os
from pathlib import Path
from obsidianpilot.tools.note_management import (
    edit_note_section,
    edit_note_content,
    _detect_frontmatter,
    _find_section_boundaries,
    _create_section_content
)
from obsidianpilot.utils.filesystem import ObsidianVault


@pytest.fixture
def temp_vault():
    """Create a temporary vault for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        
        # Set environment variable for vault path
        original_env = os.environ.get("OBSIDIAN_VAULT_PATH")
        os.environ["OBSIDIAN_VAULT_PATH"] = str(vault_path)
        
        yield vault_path
        
        # Restore original environment
        if original_env:
            os.environ["OBSIDIAN_VAULT_PATH"] = original_env
        else:
            os.environ.pop("OBSIDIAN_VAULT_PATH", None)


@pytest.fixture
async def vault_with_notes(temp_vault):
    """Create a vault with test notes."""
    vault = ObsidianVault(vault_path=str(temp_vault))
    
    # Create test notes
    test_note_content = """---
title: Test Note
tags: [test, example]
priority: high
---

# Test Note

## Introduction
This is a test note for section editing.

## Tasks
- [ ] Task 1
- [ ] Task 2

## Status
Current status: In Progress

### Details
Some detailed information here.

## Conclusion
Final thoughts."""

    frontmatter_note_content = """---
title: Simple Note
author: Test User
created: 2024-01-15
---

# Simple Note
Just some content."""

    no_frontmatter_content = """# No Frontmatter Note

## Section One
Content in section one.

## Section Two
Content in section two."""

    await vault.write_note("test_note.md", test_note_content)
    await vault.write_note("frontmatter_note.md", frontmatter_note_content)
    await vault.write_note("no_frontmatter.md", no_frontmatter_content)
    
    return vault


class TestFrontmatterDetection:
    """Test frontmatter detection helper function."""
    
    def test_detect_frontmatter_with_valid_frontmatter(self):
        content = """---
title: Test
tags: [test]
---

# Content here"""
        
        frontmatter, main_content, separator = _detect_frontmatter(content)
        
        assert frontmatter == "---\ntitle: Test\ntags: [test]\n---"
        assert main_content == "\n# Content here"
        assert separator == "\n"
    
    def test_detect_frontmatter_no_frontmatter(self):
        content = "# Just content\n\nNo frontmatter here."
        
        frontmatter, main_content, separator = _detect_frontmatter(content)
        
        assert frontmatter == ""
        assert main_content == content
        assert separator == ""
    
    def test_detect_frontmatter_invalid_frontmatter(self):
        content = """---
title: Test
no closing marker

# Content here"""
        
        frontmatter, main_content, separator = _detect_frontmatter(content)
        
        # Should treat as no frontmatter when closing marker is missing
        assert frontmatter == ""
        assert main_content == content
        assert separator == ""


class TestSectionBoundaries:
    """Test section boundary detection."""
    
    def test_find_section_boundaries_basic(self):
        content = """# Heading 1

Content 1

## Heading 2

Content 2

## Heading 3

Content 3"""
        
        start, end, heading = _find_section_boundaries(content, "## Heading 2")
        
        assert start == 3  # Line index of "## Heading 2"
        assert end == 7    # Line index before "## Heading 3"
        assert heading == "## Heading 2"
    
    def test_find_section_boundaries_case_insensitive(self):
        content = """## Tasks

- Task 1
- Task 2

## Status

Current status"""
        
        start, end, heading = _find_section_boundaries(content, "## tasks")
        
        assert start == 0
        assert end == 4
        assert heading == "## Tasks"
    
    def test_find_section_boundaries_not_found(self):
        content = """## Section A

Content A

## Section B

Content B"""
        
        start, end, heading = _find_section_boundaries(content, "## Section C")
        
        assert start is None
        assert end is None
        assert heading is None
    
    def test_find_section_boundaries_last_section(self):
        content = """## Section A

Content A

## Section B

Content B
More content"""
        
        start, end, heading = _find_section_boundaries(content, "## Section B")
        
        assert start == 3
        assert end == 7  # End of file
        assert heading == "## Section B"


class TestSectionEditing:
    """Test section editing functionality."""
    
    @pytest.mark.asyncio
    async def test_edit_section_append_to_section(self, vault_with_notes):
        """Test appending content to an existing section."""
        result = await edit_note_section(
            "test_note.md",
            "## Tasks",
            "- [ ] Task 3\n- [ ] Task 4",
            operation="append_to_section"
        )
        
        assert result["success"] is True
        assert result["operation"] == "section_edited"
        assert result["details"]["edit_operation"] == "appended"
        assert result["details"]["section_created"] is False
        
        # Verify the content was added
        vault = vault_with_notes
        note = await vault.read_note("test_note.md")
        assert "- [ ] Task 3" in note.content
        assert "- [ ] Task 4" in note.content
        # Ensure frontmatter is preserved
        assert "title: Test Note" in note.content
    
    @pytest.mark.asyncio
    async def test_edit_section_insert_after(self, vault_with_notes):
        """Test inserting content after a section heading."""
        result = await edit_note_section(
            "test_note.md",
            "## Introduction",
            "Additional introduction text.",
            operation="insert_after"
        )
        
        assert result["success"] is True
        assert result["details"]["edit_operation"] == "inserted_after"
        
        # Verify content was inserted
        vault = vault_with_notes
        note = await vault.read_note("test_note.md")
        content_lines = note.content.split('\n')
        
        # Find the Introduction section
        intro_line = None
        for i, line in enumerate(content_lines):
            if line.strip() == "## Introduction":
                intro_line = i
                break
        
        assert intro_line is not None
        assert content_lines[intro_line + 1] == "Additional introduction text."
    
    @pytest.mark.asyncio
    async def test_edit_section_edit_heading(self, vault_with_notes):
        """Test changing just a section heading."""
        result = await edit_note_section(
            "test_note.md",
            "## Tasks",
            "## Action Items",
            operation="edit_heading"
        )
        
        assert result["success"] is True
        assert result["details"]["edit_operation"] == "heading_edited"
        
        # Verify heading was changed but content preserved
        vault = vault_with_notes
        note = await vault.read_note("test_note.md")
        assert "## Action Items" in note.content
        assert "## Tasks" not in note.content
        assert "- [ ] Task 1" in note.content  # Content preserved
    
    @pytest.mark.asyncio
    async def test_edit_section_create_new_section(self, vault_with_notes):
        """Test creating a new section when it doesn't exist."""
        result = await edit_note_section(
            "test_note.md",
            "## New Section",
            "This is new content.",
            operation="insert_after",
            create_if_missing=True
        )
        
        assert result["success"] is True
        assert result["details"]["section_created"] is True
        assert result["details"]["edit_operation"] == "created"
        
        # Verify section was created
        vault = vault_with_notes
        note = await vault.read_note("test_note.md")
        assert "## New Section" in note.content
        assert "This is new content." in note.content
    
    @pytest.mark.asyncio
    async def test_edit_section_preserve_frontmatter(self, vault_with_notes):
        """Test that frontmatter is preserved during section editing."""
        result = await edit_note_section(
            "frontmatter_note.md",
            "# Simple Note",
            "Updated content.",
            operation="insert_after"
        )
        
        assert result["success"] is True
        assert result["details"]["frontmatter_preserved"] is True
        
        # Verify frontmatter is preserved
        vault = vault_with_notes
        note = await vault.read_note("frontmatter_note.md")
        assert "title: Simple Note" in note.content
        assert "author: Test User" in note.content
        assert "Updated content." in note.content


class TestContentEditing:
    """Test content editing functionality."""
    
    @pytest.mark.asyncio
    async def test_edit_content_first_occurrence(self, vault_with_notes):
        """Test replacing first occurrence of text."""
        result = await edit_note_content(
            "test_note.md",
            "In Progress",
            "Completed",
            occurrence="first"
        )
        
        assert result["success"] is True
        assert result["operation"] == "content_edited"
        assert result["details"]["replacements_made"] == 1
        
        # Verify replacement
        vault = vault_with_notes
        note = await vault.read_note("test_note.md")
        assert "Current status: Completed" in note.content
        assert "Current status: In Progress" not in note.content
    
    @pytest.mark.asyncio
    async def test_edit_content_all_occurrences(self, vault_with_notes):
        """Test replacing all occurrences of text."""
        # First add duplicate text
        await edit_note_section(
            "test_note.md",
            "## Conclusion",
            "Status: In Progress again",
            operation="append_to_section"
        )
        
        result = await edit_note_content(
            "test_note.md",
            "In Progress",
            "Completed",
            occurrence="all"
        )
        
        assert result["success"] is True
        assert result["details"]["replacements_made"] == 2  # Should replace both
        
        # Verify all replacements
        vault = vault_with_notes
        note = await vault.read_note("test_note.md")
        assert note.content.count("Completed") == 2
        assert "In Progress" not in note.content
    
    @pytest.mark.asyncio
    async def test_edit_content_text_not_found(self, vault_with_notes):
        """Test error when search text is not found."""
        with pytest.raises(ValueError, match="Search text not found"):
            await edit_note_content(
                "test_note.md",
                "Non-existent text",
                "Replacement"
            )
    
    @pytest.mark.asyncio
    async def test_edit_content_frontmatter_property(self, vault_with_notes):
        """Test editing frontmatter properties."""
        result = await edit_note_content(
            "frontmatter_note.md",
            "author: Test User",
            "author: Updated User"
        )
        
        assert result["success"] is True
        assert result["details"]["replacements_made"] == 1
        
        # Verify frontmatter was updated
        vault = vault_with_notes
        note = await vault.read_note("frontmatter_note.md")
        assert "author: Updated User" in note.content
        assert "author: Test User" not in note.content


class TestCreateSectionContent:
    """Test section content creation helper."""
    
    def test_create_section_content_with_content(self):
        result = _create_section_content("New Section", "Some content here", 2)
        expected = "## New Section\n\nSome content here"
        assert result == expected
    
    def test_create_section_content_no_content(self):
        result = _create_section_content("Empty Section", "", 3)
        expected = "### Empty Section\n"
        assert result == expected
    
    def test_create_section_content_whitespace_content(self):
        result = _create_section_content("Section", "   \n  ", 1)
        expected = "# Section\n"
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__])