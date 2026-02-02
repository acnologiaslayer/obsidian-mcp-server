"""Tests for the VaultManager class."""

import tempfile
from pathlib import Path

import pytest

from vault_manager import VaultManager


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory with sample notes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        vault_path = Path(tmp_dir)

        # Create directory structure
        (vault_path / "Daily").mkdir()
        (vault_path / "Projects").mkdir()
        (vault_path / "Projects" / "Subproject").mkdir()

        # Create sample notes
        (vault_path / "README.md").write_text("""---
title: Welcome
tags:
  - welcome
  - overview
---

# Welcome to My Vault

This is the main readme file.
""")

        (vault_path / "Daily" / "2024-01-01.md").write_text("""---
date: 2024-01-01
tags:
  - daily
---

# January 1, 2024

Daily note content.
""")

        (vault_path / "Projects" / "Project A.md").write_text("""---
status: active
tags:
  - project
  - active
---

# Project A

This project links to [[README]] and [[Project B]].

## Tasks

- [ ] Task 1
- [ ] Task 2
""")

        (vault_path / "Projects" / "Project B.md").write_text("""---
status: planning
tags:
  - project
  - planning
---

# Project B

This project references [[Project A]] for context.

Some content with #customtag.
""")

        (vault_path / "Projects" / "Subproject" / "Sub.md").write_text("""---
parent: Project A
---

# Subproject

This is a subproject note.
""")

        (vault_path / "Untagged.md").write_text("""# Untagged Note

This note has no frontmatter but has #test content.
""")

        yield vault_path


@pytest.fixture
def vault_manager(temp_vault):
    """Create a VaultManager instance with the temp vault."""
    return VaultManager(temp_vault)


class TestVaultManagerInit:
    """Tests for VaultManager initialization."""

    def test_valid_vault_path(self, temp_vault):
        """Test initializing with a valid vault path."""
        vm = VaultManager(temp_vault)
        assert vm.vault_path == temp_vault.resolve()

    def test_nonexistent_path(self):
        """Test initializing with non-existent path raises error."""
        with pytest.raises(ValueError, match="Vault path does not exist"):
            VaultManager("/nonexistent/path/12345")

    def test_file_instead_of_directory(self, temp_vault):
        """Test initializing with a file path raises error."""
        with pytest.raises(ValueError, match="Vault path is not a directory"):
            VaultManager(temp_vault / "README.md")


class TestReadNote:
    """Tests for read_note method."""

    def test_read_existing_note(self, vault_manager):
        """Test reading an existing note."""
        content = vault_manager.read_note("README.md")
        assert "Welcome to My Vault" in content
        assert "title: Welcome" in content

    def test_read_nested_note(self, vault_manager):
        """Test reading a note in a subdirectory."""
        content = vault_manager.read_note("Daily/2024-01-01.md")
        assert "January 1, 2024" in content

    def test_read_nonexistent_note(self, vault_manager):
        """Test reading a non-existent note raises error."""
        with pytest.raises(FileNotFoundError, match="Note not found"):
            vault_manager.read_note("nonexistent.md")

    def test_path_traversal_blocked(self, vault_manager):
        """Test that path traversal is blocked."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            vault_manager.read_note("../outside_vault.md")


class TestCreateNote:
    """Tests for create_note method."""

    def test_create_simple_note(self, vault_manager):
        """Test creating a note without frontmatter."""
        vault_manager.create_note("New Note.md", "Content here")
        assert (vault_manager.vault_path / "New Note.md").exists()
        content = (vault_manager.vault_path / "New Note.md").read_text()
        assert content == "Content here"

    def test_create_note_with_frontmatter(self, vault_manager):
        """Test creating a note with frontmatter."""
        vault_manager.create_note(
            "New Note.md",
            "Content here",
            {"title": "New Note", "tags": ["new"]}
        )
        content = (vault_manager.vault_path / "New Note.md").read_text()
        assert "title: New Note" in content
        assert "Content here" in content

    def test_create_in_subdirectory(self, vault_manager):
        """Test creating a note in a subdirectory."""
        vault_manager.create_note("Daily/New.md", "Daily content")
        assert (vault_manager.vault_path / "Daily" / "New.md").exists()

    def test_create_creates_directories(self, vault_manager):
        """Test that create_note creates parent directories."""
        vault_manager.create_note("New/Deep/Path/Note.md", "Deep content")
        assert (vault_manager.vault_path / "New" / "Deep" / "Path" / "Note.md").exists()

    def test_create_existing_note_raises_error(self, vault_manager):
        """Test that creating an existing note raises error."""
        with pytest.raises(FileExistsError, match="Note already exists"):
            vault_manager.create_note("README.md", "New content")


class TestEditNote:
    """Tests for edit_note method."""

    def test_edit_preserves_frontmatter(self, vault_manager):
        """Test that edit preserves frontmatter."""
        vault_manager.edit_note("README.md", "New body content")
        content = (vault_manager.vault_path / "README.md").read_text()
        assert "title: Welcome" in content  # Frontmatter preserved
        assert "New body content" in content  # New content added

    def test_edit_note_without_frontmatter(self, vault_manager):
        """Test editing a note without frontmatter."""
        vault_manager.edit_note("Untagged.md", "Updated content")
        content = (vault_manager.vault_path / "Untagged.md").read_text()
        assert content == "Updated content"

    def test_edit_nonexistent_note_raises_error(self, vault_manager):
        """Test editing non-existent note raises error."""
        with pytest.raises(FileNotFoundError, match="Note not found"):
            vault_manager.edit_note("nonexistent.md", "content")


class TestListNotes:
    """Tests for list_notes method."""

    def test_list_all_notes(self, vault_manager):
        """Test listing all notes in vault."""
        notes = vault_manager.list_notes()
        paths = {n["path"] for n in notes}
        assert "README.md" in paths
        assert "Daily/2024-01-01.md" in paths
        assert "Projects/Project A.md" in paths

    def test_list_subdirectory(self, vault_manager):
        """Test listing notes in a subdirectory."""
        notes = vault_manager.list_notes("Projects")
        paths = {n["path"] for n in notes}
        assert "Projects/Project A.md" in paths
        assert "Projects/Subproject/Sub.md" in paths
        assert "README.md" not in paths

    def test_list_nonexistent_directory(self, vault_manager):
        """Test listing non-existent directory returns empty list."""
        notes = vault_manager.list_notes("nonexistent")
        assert notes == []


class TestSearchVault:
    """Tests for search_vault method."""

    def test_search_finds_content(self, vault_manager):
        """Test searching finds notes with matching content."""
        results = vault_manager.search_vault("January")
        assert len(results) == 1
        assert results[0]["name"] == "2024-01-01"

    def test_search_case_insensitive(self, vault_manager):
        """Test searching is case-insensitive."""
        results_lower = vault_manager.search_vault("january")
        results_upper = vault_manager.search_vault("JANUARY")
        assert len(results_lower) == len(results_upper) == 1

    def test_search_returns_excerpt(self, vault_manager):
        """Test search returns excerpt around match."""
        results = vault_manager.search_vault("Welcome")
        assert len(results) == 1
        assert "excerpt" in results[0]
        assert "..." in results[0]["excerpt"]

    def test_search_no_results(self, vault_manager):
        """Test searching for non-existent content."""
        results = vault_manager.search_vault("xyznonexistent123")
        assert results == []


class TestGetVaultStructure:
    """Tests for get_vault_structure method."""

    def test_structure_includes_directories(self, vault_manager):
        """Test structure includes directories."""
        structure = vault_manager.get_vault_structure()
        assert structure["type"] == "directory"

    def test_structure_includes_notes(self, vault_manager):
        """Test structure includes notes."""
        structure = vault_manager.get_vault_structure()
        children = structure["children"]
        note_names = {c["name"] for c in children if c["type"] == "note"}
        assert "README.md" in note_names

    def test_structure_nested(self, vault_manager):
        """Test structure includes nested directories."""
        structure = vault_manager.get_vault_structure()
        project_dir = next(
            (c for c in structure["children"]
             if c["type"] == "directory" and c["name"] == "Projects"),
            None
        )
        assert project_dir is not None
        assert any(c["name"] == "Subproject" for c in project_dir["children"])


class TestReadFrontmatter:
    """Tests for read_frontmatter method."""

    def test_read_frontmatter(self, vault_manager):
        """Test reading frontmatter from note."""
        fm = vault_manager.read_frontmatter("README.md")
        assert fm["title"] == "Welcome"
        assert "welcome" in fm["tags"]

    def test_read_empty_frontmatter(self, vault_manager):
        """Test reading note without frontmatter."""
        fm = vault_manager.read_frontmatter("Untagged.md")
        assert fm == {}

    def test_read_nonexistent_note(self, vault_manager):
        """Test reading frontmatter from non-existent note."""
        with pytest.raises(FileNotFoundError):
            vault_manager.read_frontmatter("nonexistent.md")


class TestUpdateFrontmatter:
    """Tests for update_frontmatter method."""

    def test_update_frontmatter(self, vault_manager):
        """Test updating frontmatter fields."""
        vault_manager.update_frontmatter("README.md", {"author": "Test"})
        fm = vault_manager.read_frontmatter("README.md")
        assert fm["author"] == "Test"
        assert fm["title"] == "Welcome"  # Original preserved

    def test_update_overwrites_existing(self, vault_manager):
        """Test that update overwrites existing keys."""
        vault_manager.update_frontmatter("README.md", {"title": "New Title"})
        fm = vault_manager.read_frontmatter("README.md")
        assert fm["title"] == "New Title"

    def test_update_nonexistent_note(self, vault_manager):
        """Test updating frontmatter on non-existent note."""
        with pytest.raises(FileNotFoundError):
            vault_manager.update_frontmatter("nonexistent.md", {"key": "value"})


class TestGetBacklinks:
    """Tests for get_backlinks method."""

    def test_find_backlinks(self, vault_manager):
        """Test finding notes that link to a target."""
        backlinks = vault_manager.get_backlinks("Project A")
        assert len(backlinks) == 1
        assert backlinks[0]["name"] == "Project B"
        assert backlinks[0]["link_count"] == 1

    def test_count_multiple_links(self, vault_manager):
        """Test counting multiple links from same note."""
        backlinks = vault_manager.get_backlinks("README")
        # Project A links to README and Project B
        readme_backlinks = [b for b in backlinks if b["name"] == "Project A"]
        assert len(readme_backlinks) == 1
        # Should count 1 link to README
        assert readme_backlinks[0]["link_count"] >= 1

    def test_no_backlinks(self, vault_manager):
        """Test finding backlinks for note with no links to it."""
        backlinks = vault_manager.get_backlinks("NonexistentNote")
        assert backlinks == []


class TestListTags:
    """Tests for list_tags method."""

    def test_list_all_tags(self, vault_manager):
        """Test listing all tags in vault."""
        tags = vault_manager.list_tags()
        tag_names = {t["tag"] for t in tags}
        assert "welcome" in tag_names
        assert "project" in tag_names
        assert "daily" in tag_names

    def test_tag_counts(self, vault_manager):
        """Test that tag counts are correct."""
        tags = vault_manager.list_tags()
        tag_dict = {t["tag"]: t for t in tags}
        # 'project' tag appears in Project A and Project B
        assert tag_dict["project"]["count"] == 2

    def test_tag_examples(self, vault_manager):
        """Test that tag examples are provided."""
        tags = vault_manager.list_tags()
        for tag in tags:
            assert "examples" in tag
            assert isinstance(tag["examples"], list)


class TestFindByTag:
    """Tests for find_by_tag method."""

    def test_find_by_tag(self, vault_manager):
        """Test finding notes by tag."""
        results = vault_manager.find_by_tag("project")
        assert len(results) == 2
        paths = {r["path"] for r in results}
        assert "Projects/Project A.md" in paths
        assert "Projects/Project B.md" in paths

    def test_find_by_tag_with_hash(self, vault_manager):
        """Test finding notes with # prefix in tag."""
        results = vault_manager.find_by_tag("#project")
        assert len(results) == 2

    def test_find_by_tag_partial_match_blocked(self, vault_manager):
        """Test that partial tag matches are blocked."""
        # Should not match "customtag" when searching for "custom"
        results = vault_manager.find_by_tag("custom")
        assert len(results) == 0  # customtag requires full match

    def test_find_nonexistent_tag(self, vault_manager):
        """Test finding notes with non-existent tag."""
        results = vault_manager.find_by_tag("nonexistent")
        assert results == []
