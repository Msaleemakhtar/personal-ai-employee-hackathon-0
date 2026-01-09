"""YAML frontmatter parsing utilities.

This module provides proper YAML parsing for markdown files with frontmatter,
replacing hand-rolled regex-based parsers that can fail with special characters.
"""

from __future__ import annotations

import yaml


def parse_frontmatter(content: str) -> dict[str, str | int | bool]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Dictionary of frontmatter key-value pairs (empty if no frontmatter)

    Example:
        >>> content = '''---
        ... type: email
        ... priority: high
        ... ---
        ... # Email Body
        ... Hello world
        ... '''
        >>> parse_frontmatter(content)
        {'type': 'email', 'priority': 'high'}
    """
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter_text = parts[1].strip()
    try:
        metadata = yaml.safe_load(frontmatter_text)
        return metadata if isinstance(metadata, dict) else {}
    except yaml.YAMLError:
        return {}


def extract_body(content: str) -> str:
    """Extract markdown body content after frontmatter.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Body content with frontmatter removed

    Example:
        >>> content = '''---
        ... type: email
        ... ---
        ... # Email Body
        ... Hello world
        ... '''
        >>> extract_body(content)
        '# Email Body\\nHello world\\n'
    """
    if not content.startswith("---"):
        return content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    return parts[2].strip()


def update_frontmatter(content: str, updates: dict[str, str | int | bool]) -> str:
    """Update frontmatter fields while preserving body.

    Args:
        content: Markdown content with optional YAML frontmatter
        updates: Dictionary of fields to update

    Returns:
        Updated markdown content

    Example:
        >>> content = '''---
        ... status: pending
        ... ---
        ... # Body
        ... '''
        >>> update_frontmatter(content, {'status': 'done'})
        '---\\nstatus: done\\n---\\n\\n# Body'
    """
    metadata = parse_frontmatter(content)
    body = extract_body(content)

    # Merge updates
    metadata.update(updates)

    # Rebuild content
    frontmatter_yaml = yaml.safe_dump(metadata, default_flow_style=False, sort_keys=False)
    return f"---\n{frontmatter_yaml}---\n\n{body}"
