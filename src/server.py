#!/usr/bin/env python3
"""Obsidian MCP Server - A Model Context Protocol server for Obsidian vault integration.

This server provides tools for interacting with Obsidian vaults, including reading,
writing, searching, and analyzing notes.

Environment Variables:
    VAULT_PATH: Path to the Obsidian vault directory (required).
    TRANSPORT: Transport mode - "stdio" (default) or "sse".
    LOG_LEVEL: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO).
    HOST: Host to bind SSE server to (default: 0.0.0.0).
    PORT: Port to bind SSE server to (default: 3000).
"""

import json
import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from vault_manager import VaultManager

# Configure logging to stderr (stdout is reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("obsidian-mcp")

# Get configuration from environment
VAULT_PATH = os.environ.get("VAULT_PATH")
TRANSPORT = os.environ.get("TRANSPORT", "stdio").lower()
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "3000"))

# Set log level
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Validate vault path
if not VAULT_PATH:
    logger.error("VAULT_PATH environment variable is required")
    sys.exit(1)

try:
    vault = VaultManager(VAULT_PATH)
    logger.info(f"Connected to vault: {VAULT_PATH}")
except ValueError as e:
    logger.error(f"Failed to initialize vault manager: {e}")
    sys.exit(1)

# Initialize MCP server
mcp = FastMCP("obsidian-mcp-server")


@mcp.tool()
def read_note(filepath: str) -> str:
    """Read the full content of an Obsidian note.

    Args:
        filepath: Relative path to the note within the vault (e.g., "Daily/2024-01-01.md").

    Returns:
        The full text content of the note including frontmatter.

    Raises:
        FileNotFoundError: If the note does not exist.
        ValueError: If the path is outside the vault.
    """
    logger.debug(f"Reading note: {filepath}")
    return vault.read_note(filepath)


@mcp.tool()
def create_note(
    filepath: str,
    content: str,
    frontmatter: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Create a new note in the Obsidian vault.

    Args:
        filepath: Relative path for the new note (e.g., "Projects/New Project.md").
        content: The note body content (Markdown format).
        frontmatter: Optional YAML frontmatter dictionary with metadata
            (e.g., {"tags": ["project"], "created": "2024-01-01"}).

    Returns:
        Dictionary with success message and note path.

    Raises:
        FileExistsError: If a note already exists at the specified path.
        ValueError: If the path is outside the vault.
    """
    logger.debug(f"Creating note: {filepath}")
    vault.create_note(filepath, content, frontmatter)
    return {"message": "Note created successfully", "path": filepath}


@mcp.tool()
def edit_note(filepath: str, content: str) -> dict[str, str]:
    """Edit an existing note while preserving its frontmatter.

    This tool updates only the body content of a note. Any existing YAML
    frontmatter will be preserved unchanged.

    Args:
        filepath: Relative path to the existing note.
        content: New body content for the note (Markdown format).

    Returns:
        Dictionary with success message and note path.

    Raises:
        FileNotFoundError: If the note does not exist.
        ValueError: If the path is outside the vault.
    """
    logger.debug(f"Editing note: {filepath}")
    vault.edit_note(filepath, content)
    return {"message": "Note updated successfully", "path": filepath}


@mcp.tool()
def list_notes(directory: str = ".") -> list[dict[str, Any]]:
    """List all markdown notes in a directory.

    Recursively finds all .md files in the specified directory and returns
    metadata for each note.

    Args:
        directory: Relative path to the directory (default: vault root).
            Use "." for root, or subdirectories like "Daily", "Projects".

    Returns:
        List of note metadata dictionaries containing:
        - path: Relative path to the note
        - name: Note name (without .md extension)
        - size: File size in bytes
        - modified: Last modification timestamp
    """
    logger.debug(f"Listing notes in: {directory}")
    return vault.list_notes(directory)


@mcp.tool()
def search_vault(query: str) -> list[dict[str, Any]]:
    """Search all notes for content matching a query string.

    Performs a case-insensitive search across all notes in the vault
    and returns matching notes with contextual excerpts.

    Args:
        query: Search string to find in note content.

    Returns:
        List of matching notes with metadata:
        - path: Relative path to the note
        - name: Note name
        - excerpt: Text excerpt around the match (200 chars context)
    """
    logger.debug(f"Searching vault for: {query}")
    return vault.search_vault(query)


@mcp.tool()
def get_vault_structure() -> dict[str, Any]:
    """Get the complete directory tree structure of the vault.

    Returns a hierarchical representation of all directories and markdown
    notes in the vault, useful for understanding the vault organization.

    Returns:
        Nested dictionary with structure:
        - name: Directory or file name
        - type: "directory" or "note"
        - path: (for notes) Relative path
        - children: (for directories) List of child items
    """
    logger.debug("Getting vault structure")
    return vault.get_vault_structure()


@mcp.tool()
def read_frontmatter(filepath: str) -> dict[str, Any]:
    """Parse and extract YAML frontmatter from a note.

    Reads the YAML frontmatter (delimited by ---) from the top of a note
    and returns it as a dictionary.

    Args:
        filepath: Relative path to the note.

    Returns:
        Dictionary of frontmatter fields. Returns empty dict if no frontmatter.

    Raises:
        FileNotFoundError: If the note does not exist.
        ValueError: If the frontmatter contains invalid YAML.
    """
    logger.debug(f"Reading frontmatter from: {filepath}")
    return vault.read_frontmatter(filepath)


@mcp.tool()
def update_frontmatter(
    filepath: str,
    frontmatter: dict[str, Any],
) -> dict[str, str]:
    """Update the YAML frontmatter of an existing note.

    Merges the provided frontmatter with existing frontmatter. New values
    will overwrite existing ones with the same keys.

    Args:
        filepath: Relative path to the note.
        frontmatter: Dictionary of frontmatter fields to set or update.

    Returns:
        Dictionary with success message and note path.

    Raises:
        FileNotFoundError: If the note does not exist.
        ValueError: If the frontmatter contains invalid YAML.
    """
    logger.debug(f"Updating frontmatter for: {filepath}")
    vault.update_frontmatter(filepath, frontmatter)
    return {"message": "Frontmatter updated successfully", "path": filepath}


@mcp.tool()
def get_backlinks(note_name: str) -> list[dict[str, Any]]:
    """Find all notes that link to a specific note.

    Searches the entire vault for wiki-style links [[note_name]] pointing
    to the specified note.

    Args:
        note_name: Name of the target note (without .md extension).
            Example: "My Note" to find [[My Note]] links.

    Returns:
        List of notes containing backlinks:
        - path: Relative path to the linking note
        - name: Name of the linking note
        - link_count: Number of links to the target in this note
    """
    logger.debug(f"Finding backlinks for: {note_name}")
    return vault.get_backlinks(note_name)


@mcp.tool()
def list_tags() -> list[dict[str, Any]]:
    """List all unique tags found across the entire vault.

    Scans all notes for hashtags (#tag) and returns a summary of tag usage.

    Returns:
        List of tag information dictionaries:
        - tag: Tag name (without # prefix)
        - count: Number of notes containing this tag
        - examples: List of up to 3 example note paths
    """
    logger.debug("Listing all tags in vault")
    return vault.list_tags()


@mcp.tool()
def find_by_tag(tag: str) -> list[dict[str, Any]]:
    """Find all notes containing a specific hashtag.

    Args:
        tag: Tag to search for (with or without # prefix).
            Examples: "project", "#project"

    Returns:
        List of notes containing the tag:
        - path: Relative path to the note
        - name: Note name (without .md extension)
    """
    logger.debug(f"Finding notes with tag: {tag}")
    return vault.find_by_tag(tag)


def main() -> None:
    """Run the MCP server with the configured transport."""
    logger.info(f"Starting Obsidian MCP Server with {TRANSPORT} transport")

    if TRANSPORT == "sse":
        # Run with SSE transport for remote connections
        mcp.run(transport="sse", host=HOST, port=PORT)
    else:
        # Run with stdio transport (default for Claude Desktop)
        mcp.run()


if __name__ == "__main__":
    main()
