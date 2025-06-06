"""Pydantic models for Obsidian data structures."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class NoteMetadata(BaseModel):
    """Metadata for an Obsidian note."""
    
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    tags: List[str] = Field(default_factory=list, description="List of tags")
    aliases: List[str] = Field(default_factory=list, description="Alternative names for the note")
    frontmatter: Dict[str, Any] = Field(default_factory=dict, description="Raw frontmatter data")


class Note(BaseModel):
    """Represents an Obsidian note."""
    
    path: str = Field(..., description="Path to the note relative to vault root")
    content: str = Field(..., description="Markdown content of the note")
    metadata: NoteMetadata = Field(default_factory=NoteMetadata, description="Note metadata")
    
    @validator("path")
    def validate_path(cls, v):
        """Ensure path doesn't contain invalid characters."""
        if not v or ".." in v:
            raise ValueError("Invalid path")
        return v.strip("/")


class VaultItem(BaseModel):
    """Represents an item in the vault (file or folder)."""
    
    path: str = Field(..., description="Path relative to vault root")
    name: str = Field(..., description="Name of the file or folder")
    is_folder: bool = Field(..., description="Whether this is a folder")
    children: Optional[List["VaultItem"]] = Field(None, description="Child items if this is a folder")


class SearchResult(BaseModel):
    """Result from a search operation."""
    
    path: str = Field(..., description="Path to the matching note")
    score: float = Field(..., description="Relevance score")
    matches: List[str] = Field(default_factory=list, description="Matching text excerpts")
    context: Optional[str] = Field(None, description="Context around the match")


class Tag(BaseModel):
    """Represents a tag in the vault."""
    
    name: str = Field(..., description="Tag name without the # prefix")
    count: int = Field(default=0, description="Number of notes with this tag")
    notes: List[str] = Field(default_factory=list, description="Paths to notes with this tag")
    
    @validator("name")
    def clean_tag_name(cls, v):
        """Remove # prefix if present."""
        return v.lstrip("#")


class Backlink(BaseModel):
    """Represents a backlink to a note."""
    
    source_path: str = Field(..., description="Path of the note containing the link")
    link_text: str = Field(..., description="Text of the link")
    context: Optional[str] = Field(None, description="Text around the link for context")


# Enable forward references
VaultItem.model_rebuild()