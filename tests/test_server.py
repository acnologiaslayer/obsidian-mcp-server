"""Tests for the MCP server tools."""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import after setting up path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory with sample notes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        vault_path = Path(tmp_dir)

        # Create sample notes
        (vault_path / "Daily").mkdir()
        (vault_path / "README.md").write_text("""---
title: Welcome
tags:
  - welcome
---

# Welcome

Test vault.
""")
        (vault_path / "Daily" / "2024-01-01.md").write_text("""---
date: 2024-01-01
---

Daily note.
""")

        # Store original env
        original_vault = os.environ.get("VAULT_PATH")
        os.environ["VAULT_PATH"] = str(vault_path)
        os.environ["TRANSPORT"] = "stdio"
        os.environ["LOG_LEVEL"] = "ERROR"

        yield vault_path

        # Restore original env
        if original_vault:
            os.environ["VAULT_PATH"] = original_vault
        else:
            del os.environ["VAULT_PATH"]
        del os.environ["TRANSPORT"]
        del os.environ["LOG_LEVEL"]


@pytest.fixture
def server_module(temp_vault):
    """Import and return the server module with tools."""
    # Import after environment is set
    import server
    return server


class TestReadNote:
    """Tests for read_note tool."""

    def test_read_note_returns_content(self, server_module):
        """Test read_note returns note content."""
        result = server_module.read_note("README.md")
        assert "Welcome" in result
        assert "title: Welcome" in result

    def test_read_note_not_found(self, server_module):
        """Test read_note raises error for missing note."""
        with pytest.raises(FileNotFoundError):
            server_module.read_note("nonexistent.md")


class TestCreateNote:
    """Tests for create_note tool."""

    def test_create_note_success(self, server_module, temp_vault):
        """Test create_note creates a note successfully."""
        result = server_module.create_note("New.md", "Content")
        assert result["message"] == "Note created successfully"
        assert (temp_vault / "New.md").exists()

    def test_create_note_with_frontmatter(self, server_module, temp_vault):
        """Test create_note with frontmatter."""
        server_module.create_note("New.md", "Body", {"title": "Test"})
        content = (temp_vault / "New.md").read_text()
        assert "title: Test" in content
        assert "Body" in content

    def test_create_note_already_exists(self, server_module):
        """Test create_note fails if note exists."""
        with pytest.raises(FileExistsError):
            server_module.create_note("README.md", "Content")


class TestEditNote:
    """Tests for edit_note tool."""

    def test_edit_note_preserves_frontmatter(self, server_module, temp_vault):
        """Test edit_note preserves frontmatter."""
        server_module.edit_note("README.md", "New content")
        content = (temp_vault / "README.md").read_text()
        assert "title: Welcome" in content
        assert "New content" in content

    def test_edit_note_not_found(self, server_module):
        """Test edit_note fails for missing note."""
        with pytest.raises(FileNotFoundError):
            server_module.edit_note("nonexistent.md", "Content")


class TestListNotes:
    """Tests for list_notes tool."""

    def test_list_notes_returns_list(self, server_module):
        """Test list_notes returns list of notes."""
        result = server_module.list_notes()
        assert isinstance(result, list)
        assert len(result) == 2

    def test_list_notes_subdirectory(self, server_module):
        """Test list_notes filters by directory."""
        result = server_module.list_notes("Daily")
        assert len(result) == 1
        assert result[0]["name"] == "2024-01-01"


class TestSearchVault:
    """Tests for search_vault tool."""

    def test_search_finds_matches(self, server_module):
        """Test search finds matching notes."""
        result = server_module.search_vault("Welcome")
        assert len(result) == 1
        assert result[0]["name"] == "README"

    def test_search_no_matches(self, server_module):
        """Test search returns empty for no matches."""
        result = server_module.search_vault("xyznonexistent")
        assert result == []


class TestGetVaultStructure:
    """Tests for get_vault_structure tool."""

    def test_structure_has_type(self, server_module):
        """Test structure has correct type field."""
        result = server_module.get_vault_structure()
        assert result["type"] == "directory"

    def test_structure_has_children(self, server_module):
        """Test structure includes children."""
        result = server_module.get_vault_structure()
        assert "children" in result
        assert len(result["children"]) >= 1


class TestReadFrontmatter:
    """Tests for read_frontmatter tool."""

    def test_read_frontmatter(self, server_module):
        """Test read_frontmatter returns dict."""
        result = server_module.read_frontmatter("README.md")
        assert isinstance(result, dict)
        assert result["title"] == "Welcome"

    def test_read_no_frontmatter(self, server_module, temp_vault):
        """Test read_frontmatter returns empty dict."""
        (temp_vault / "NoFront.md").write_text("# Title\nContent")
        result = server_module.read_frontmatter("NoFront.md")
        assert result == {}


class TestUpdateFrontmatter:
    """Tests for update_frontmatter tool."""

    def test_update_frontmatter(self, server_module, temp_vault):
        """Test update_frontmatter merges fields."""
        server_module.update_frontmatter("README.md", {"author": "Test"})
        result = server_module.read_frontmatter("README.md")
        assert result["author"] == "Test"
        assert result["title"] == "Welcome"

    def test_update_frontmatter_not_found(self, server_module):
        """Test update_frontmatter fails for missing note."""
        with pytest.raises(FileNotFoundError):
            server_module.update_frontmatter("nonexistent.md", {"key": "value"})


class TestGetBacklinks:
    """Tests for get_backlinks tool."""

    def test_get_backlinks(self, server_module, temp_vault):
        """Test get_backlinks finds links."""
        # Create a note with a link
        (temp_vault / "Linker.md").write_text("This links to [[README]].")
        result = server_module.get_backlinks("README")
        assert len(result) == 1
        assert result[0]["name"] == "Linker"

    def test_no_backlinks(self, server_module):
        """Test get_backlinks returns empty."""
        result = server_module.get_backlinks("Nonexistent")
        assert result == []


class TestListTags:
    """Tests for list_tags tool."""

    def test_list_tags_returns_list(self, server_module):
        """Test list_tags returns list."""
        result = server_module.list_tags()
        assert isinstance(result, list)

    def test_list_tags_has_correct_tag(self, server_module, temp_vault):
        """Test list_tags finds tags."""
        # Add note with tag
        (temp_vault / "Tagged.md").write_text("Content with #mytag here.")
        result = server_module.list_tags()
        tags = [t["tag"] for t in result]
        assert "mytag" in tags


class TestFindByTag:
    """Tests for find_by_tag tool."""

    def test_find_by_tag(self, server_module, temp_vault):
        """Test find_by_tag returns matching notes."""
        (temp_vault / "Tagged.md").write_text("Content with #testtag here.")
        result = server_module.find_by_tag("testtag")
        assert len(result) == 1
        assert result[0]["name"] == "Tagged"

    def test_find_by_tag_no_results(self, server_module):
        """Test find_by_tag returns empty."""
        result = server_module.find_by_tag("nonexistent")
        assert result == []


class TestEnvironmentValidation:
    """Tests for environment variable validation."""

    def test_missing_vault_path(self):
        """Test that missing VAULT_PATH causes exit."""
        # Remove VAULT_PATH temporarily
        original = os.environ.pop("VAULT_PATH", None)
        try:
            with pytest.raises(SystemExit):
                # Force re-import with no VAULT_PATH
                if "server" in sys.modules:
                    del sys.modules["server"]
                import server  # noqa: F401
        finally:
            if original:
                os.environ["VAULT_PATH"] = original
