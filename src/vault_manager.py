"""Obsidian vault operations manager."""

import os
import re
from pathlib import Path
from typing import Any

from frontmatter_parser import FrontmatterParser


class VaultManager:
    """Manages operations on an Obsidian vault."""

    def __init__(self, vault_path: str | Path):
        """Initialize the vault manager.

        Args:
            vault_path: Path to the Obsidian vault directory.

        Raises:
            ValueError: If the vault path does not exist.
        """
        self.vault_path = Path(vault_path).resolve()
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        if not self.vault_path.is_dir():
            raise ValueError(f"Vault path is not a directory: {self.vault_path}")

    def _resolve_path(self, filepath: str) -> Path:
        """Resolve a file path relative to the vault root.

        Args:
            filepath: Relative path within the vault.

        Returns:
            Absolute path resolved against vault root.

        Raises:
            ValueError: If the path attempts directory traversal outside vault.
        """
        filepath = filepath.lstrip("/")
        full_path = (self.vault_path / filepath).resolve()

        # Security check: ensure path is within vault
        try:
            full_path.relative_to(self.vault_path)
        except ValueError as e:
            raise ValueError(
                f"Path traversal detected: {filepath} is outside vault"
            ) from e

        return full_path

    def read_note(self, filepath: str) -> str:
        """Read the content of a note.

        Args:
            filepath: Relative path to the note within the vault.

        Returns:
            The full text content of the note.

        Raises:
            FileNotFoundError: If the note does not exist.
        """
        full_path = self._resolve_path(filepath)

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {filepath}")

        return full_path.read_text(encoding="utf-8")

    def create_note(
        self, filepath: str, content: str, frontmatter: dict[str, Any] | None = None
    ) -> None:
        """Create a new note in the vault.

        Args:
            filepath: Relative path for the new note.
            content: The note content (without frontmatter).
            frontmatter: Optional YAML frontmatter dictionary.

        Raises:
            FileExistsError: If the note already exists.
        """
        full_path = self._resolve_path(filepath)

        if full_path.exists():
            raise FileExistsError(f"Note already exists: {filepath}")

        # Ensure parent directories exist
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with frontmatter if provided
        if frontmatter:
            full_text = FrontmatterParser.dump(frontmatter, content)
        else:
            full_text = content

        full_path.write_text(full_text, encoding="utf-8")

    def edit_note(self, filepath: str, content: str) -> None:
        """Edit an existing note, preserving frontmatter.

        Args:
            filepath: Relative path to the note.
            content: New content (frontmatter will be preserved).

        Raises:
            FileNotFoundError: If the note does not exist.
        """
        full_path = self._resolve_path(filepath)

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {filepath}")

        # Read existing content to preserve frontmatter
        existing_text = full_path.read_text(encoding="utf-8")
        result = FrontmatterParser.parse(existing_text)

        # Write with preserved frontmatter
        if result.has_frontmatter:
            new_text = FrontmatterParser.dump(result.frontmatter, content)
        else:
            new_text = content

        full_path.write_text(new_text, encoding="utf-8")

    def list_notes(self, directory: str = ".") -> list[dict[str, Any]]:
        """List all markdown notes in a directory.

        Args:
            directory: Relative path to directory (default: vault root).

        Returns:
            List of note metadata dictionaries.
        """
        dir_path = self._resolve_path(directory)

        if not dir_path.exists():
            return []

        notes = []
        for md_file in sorted(dir_path.rglob("*.md")):
            try:
                rel_path = md_file.relative_to(self.vault_path).as_posix()
                stat = md_file.stat()
                notes.append({
                    "path": rel_path,
                    "name": md_file.stem,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
            except (OSError, ValueError):
                continue

        return notes

    def search_vault(self, query: str) -> list[dict[str, Any]]:
        """Search notes by content.

        Args:
            query: Search string to find in notes.

        Returns:
            List of matching notes with excerpts.
        """
        results = []
        query_lower = query.lower()

        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    rel_path = md_file.relative_to(self.vault_path).as_posix()

                    # Find excerpt around match
                    idx = content.lower().find(query_lower)
                    start = max(0, idx - 100)
                    end = min(len(content), idx + len(query) + 100)
                    excerpt = content[start:end].replace("\n", " ")

                    results.append({
                        "path": rel_path,
                        "name": md_file.stem,
                        "excerpt": f"...{excerpt}...",
                    })
            except (OSError, UnicodeDecodeError):
                continue

        return results

    def get_vault_structure(self) -> dict[str, Any]:
        """Get the full directory tree structure of the vault.

        Returns:
            Nested dictionary representing the vault structure.
        """

        def build_tree(path: Path) -> dict[str, Any]:
            result: dict[str, Any] = {
                "name": path.name or self.vault_path.name,
                "type": "directory",
                "children": [],
            }

            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith("."):
                        continue

                    if item.is_dir():
                        result["children"].append(build_tree(item))
                    elif item.suffix == ".md":
                        result["children"].append({
                            "name": item.name,
                            "type": "note",
                            "path": item.relative_to(self.vault_path).as_posix(),
                        })
            except PermissionError:
                pass

            return result

        return build_tree(self.vault_path)

    def read_frontmatter(self, filepath: str) -> dict[str, Any]:
        """Parse and return YAML frontmatter from a note.

        Args:
            filepath: Relative path to the note.

        Returns:
            Dictionary of frontmatter fields (empty if none).

        Raises:
            FileNotFoundError: If the note does not exist.
        """
        full_path = self._resolve_path(filepath)

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {filepath}")

        content = full_path.read_text(encoding="utf-8")
        result = FrontmatterParser.parse(content)

        return result.frontmatter

    def update_frontmatter(
        self, filepath: str, frontmatter: dict[str, Any]
    ) -> None:
        """Update the frontmatter of a note.

        Args:
            filepath: Relative path to the note.
            frontmatter: New frontmatter fields to set.

        Raises:
            FileNotFoundError: If the note does not exist.
        """
        full_path = self._resolve_path(filepath)

        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {filepath}")

        content = full_path.read_text(encoding="utf-8")
        new_content = FrontmatterParser.update(content, frontmatter)
        full_path.write_text(new_content, encoding="utf-8")

    def get_backlinks(self, note_name: str) -> list[dict[str, Any]]:
        """Find all notes that link to a specific note.

        Args:
            note_name: Name of the target note (without .md extension).

        Returns:
            List of notes that contain links to the target.
        """
        # Pattern matches [[note_name]] or [[note_name|alias]]
        link_pattern = re.compile(
            rf"\[\[{re.escape(note_name)}(\|[^\]]+)?\]\]"
        )

        backlinks = []

        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                matches = link_pattern.findall(content)

                if matches:
                    rel_path = md_file.relative_to(self.vault_path).as_posix()
                    backlinks.append({
                        "path": rel_path,
                        "name": md_file.stem,
                        "link_count": len(matches),
                    })
            except (OSError, UnicodeDecodeError):
                continue

        return backlinks

    def list_tags(self) -> list[dict[str, Any]]:
        """List all unique tags found in the vault.

        Returns:
            List of tags with counts and example notes.
        """
        tag_pattern = re.compile(r"#(\w+)")
        tag_data: dict[str, dict[str, Any]] = {}

        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                tags = tag_pattern.findall(content)

                rel_path = md_file.relative_to(self.vault_path).as_posix()

                for tag in tags:
                    if tag not in tag_data:
                        tag_data[tag] = {"count": 0, "examples": []}

                    tag_data[tag]["count"] += 1
                    if len(tag_data[tag]["examples"]) < 3:
                        tag_data[tag]["examples"].append(rel_path)
            except (OSError, UnicodeDecodeError):
                continue

        return [
            {"tag": tag, "count": data["count"], "examples": data["examples"]}
            for tag, data in sorted(tag_data.items(), key=lambda x: -x[1]["count"])
        ]

    def find_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Find all notes containing a specific tag.

        Args:
            tag: Tag to search for (without # prefix).

        Returns:
            List of notes containing the tag.
        """
        # Handle tag with or without hash prefix
        clean_tag = tag.lstrip("#")
        tag_pattern = re.compile(rf"#\b{re.escape(clean_tag)}\b")

        results = []

        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if tag_pattern.search(content):
                    rel_path = md_file.relative_to(self.vault_path).as_posix()
                    results.append({
                        "path": rel_path,
                        "name": md_file.stem,
                    })
            except (OSError, UnicodeDecodeError):
                continue

        return results
