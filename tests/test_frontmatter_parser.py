"""Tests for the FrontmatterParser class."""

import pytest
import yaml

from frontmatter_parser import FrontmatterParser


class TestParse:
    """Tests for the parse method."""

    def test_parse_with_frontmatter(self):
        """Test parsing text with frontmatter."""
        text = """---
title: My Note
tags:
  - tag1
  - tag2
---

# Content

Body text here.
"""
        result = FrontmatterParser.parse(text)
        assert result.has_frontmatter is True
        assert result.frontmatter["title"] == "My Note"
        assert result.frontmatter["tags"] == ["tag1", "tag2"]
        assert "# Content" in result.content
        assert "Body text here" in result.content

    def test_parse_without_frontmatter(self):
        """Test parsing text without frontmatter."""
        text = "# Just Content\n\nNo frontmatter here."
        result = FrontmatterParser.parse(text)
        assert result.has_frontmatter is False
        assert result.frontmatter == {}
        assert result.content == text

    def test_parse_empty_frontmatter(self):
        """Test parsing text with empty frontmatter."""
        text = """---
---

Content after empty frontmatter.
"""
        result = FrontmatterParser.parse(text)
        assert result.has_frontmatter is True
        assert result.frontmatter == {}
        assert "Content after" in result.content

    def test_parse_invalid_yaml(self):
        """Test parsing text with invalid YAML frontmatter."""
        text = """---
title: : invalid yaml :
---

Content
"""
        with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
            FrontmatterParser.parse(text)

    def test_parse_frontmatter_no_newline(self):
        """Test parsing with frontmatter not followed by newline."""
        text = "---\ntitle: Test\n---Content immediately after"
        result = FrontmatterParser.parse(text)
        # Should not match because no newline after ---
        assert result.has_frontmatter is False


class TestDump:
    """Tests for the dump method."""

    def test_dump_with_frontmatter(self):
        """Test dumping with frontmatter."""
        frontmatter = {"title": "Test", "date": "2024-01-01"}
        content = "# Test Content"
        result = FrontmatterParser.dump(frontmatter, content)
        assert result.startswith("---\n")
        assert "title: Test" in result
        assert "date: 2024-01-01" in result
        assert "---\n\n# Test Content" in result

    def test_dump_empty_frontmatter(self):
        """Test dumping with empty frontmatter."""
        result = FrontmatterParser.dump({}, "Content")
        assert result == "Content"

    def test_dump_no_content(self):
        """Test dumping with frontmatter but no content."""
        frontmatter = {"title": "Empty"}
        result = FrontmatterParser.dump(frontmatter, "")
        assert "title: Empty" in result
        assert result.endswith("---\n\n")


class TestUpdate:
    """Tests for the update method."""

    def test_update_frontmatter(self):
        """Test updating frontmatter while preserving content."""
        text = """---
title: Original
---

Original content.
"""
        new_frontmatter = {"author": "Test"}
        result = FrontmatterParser.update(text, new_frontmatter)
        parsed = FrontmatterParser.parse(result)
        assert parsed.frontmatter["title"] == "Original"
        assert parsed.frontmatter["author"] == "Test"
        assert "Original content" in parsed.content

    def test_update_overwrites_existing_keys(self):
        """Test that update overwrites existing keys."""
        text = """---
title: Original
---

Content
"""
        new_frontmatter = {"title": "Updated"}
        result = FrontmatterParser.update(text, new_frontmatter)
        parsed = FrontmatterParser.parse(result)
        assert parsed.frontmatter["title"] == "Updated"

    def test_update_no_existing_frontmatter(self):
        """Test updating text without existing frontmatter."""
        text = "# Just Content"
        new_frontmatter = {"title": "Added"}
        result = FrontmatterParser.update(text, new_frontmatter)
        parsed = FrontmatterParser.parse(result)
        assert parsed.frontmatter["title"] == "Added"
        assert "# Just Content" in parsed.content


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_in_frontmatter(self):
        """Test handling unicode in frontmatter."""
        text = """---
title: 日本語
emoji: 🎉
---

Content
"""
        result = FrontmatterParser.parse(text)
        assert result.frontmatter["title"] == "日本語"
        assert result.frontmatter["emoji"] == "🎉"

    def test_multiline_values(self):
        """Test handling multiline values in frontmatter."""
        text = """---
description: |
  This is a multiline
  description that spans
  multiple lines.
---

Content
"""
        result = FrontmatterParser.parse(text)
        assert "multiline" in result.frontmatter["description"]
        assert "multiple lines" in result.frontmatter["description"]

    def test_complex_nested_structure(self):
        """Test handling complex nested structures."""
        text = """---
metadata:
  author:
    name: John Doe
    email: john@example.com
  tags:
    - python
    - testing
---

Content
"""
        result = FrontmatterParser.parse(text)
        assert result.frontmatter["metadata"]["author"]["name"] == "John Doe"
        assert "python" in result.frontmatter["metadata"]["tags"]
