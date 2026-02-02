"""YAML frontmatter parser for Obsidian notes."""

import re
from dataclasses import dataclass
from typing import Any

import yaml


@dataclass
class FrontmatterResult:
    """Result of parsing frontmatter from a note."""

    frontmatter: dict[str, Any]
    content: str
    has_frontmatter: bool


class FrontmatterParser:
    """Parser for YAML frontmatter in Obsidian notes."""

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    @classmethod
    def parse(cls, text: str) -> FrontmatterResult:
        """Parse frontmatter and content from note text.

        Args:
            text: The full text of the note.

        Returns:
            FrontmatterResult containing frontmatter dict, content, and whether frontmatter was found.
        """
        match = cls.FRONTMATTER_PATTERN.match(text)

        if not match:
            return FrontmatterResult(
                frontmatter={}, content=text, has_frontmatter=False
            )

        frontmatter_text = match.group(1)
        content = text[match.end() :]

        try:
            frontmatter = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}") from e

        return FrontmatterResult(
            frontmatter=frontmatter, content=content, has_frontmatter=True
        )

    @classmethod
    def dump(cls, frontmatter: dict[str, Any], content: str) -> str:
        """Serialize frontmatter and content to note text.

        Args:
            frontmatter: Dictionary of frontmatter fields.
            content: The note content.

        Returns:
            The full note text with YAML frontmatter.
        """
        if not frontmatter:
            return content

        yaml_text = yaml.dump(
            frontmatter,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        return f"---\n{yaml_text}---\n\n{content}"

    @classmethod
    def update(cls, text: str, frontmatter: dict[str, Any]) -> str:
        """Update frontmatter while preserving content.

        Args:
            text: The full text of the note.
            frontmatter: New frontmatter dictionary to apply.

        Returns:
            The note with updated frontmatter.
        """
        result = cls.parse(text)
        merged_frontmatter = {**result.frontmatter, **frontmatter}
        return cls.dump(merged_frontmatter, result.content)
