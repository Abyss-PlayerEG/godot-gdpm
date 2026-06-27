"""Tag file utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from gdpm.constants import LOCAL_TAG_PREFIX, TAG_FILENAME

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class PluginTag:
    slug: str
    source: str
    is_local: bool


def read_plugin_tag(addon_dir: Path) -> PluginTag | None:
    """Read tag.gdpm from an addon directory.

    Returns None if tag file doesn't exist.
    """
    tag_path = addon_dir / TAG_FILENAME
    if not tag_path.exists():
        return None

    content = tag_path.read_text(encoding="utf-8").strip()
    if not content:
        return None

    is_local = content.startswith(LOCAL_TAG_PREFIX)

    slug = content.split("/")[-1] if "/" in content else content.split("+")[-1]

    return PluginTag(slug=slug, source=content, is_local=is_local)


def scan_addons(addons_dir: Path) -> list[tuple[Path, PluginTag]]:
    """Scan addons directory for tagged plugins.

    Returns list of (directory_path, tag) tuples.
    """
    if not addons_dir.exists():
        return []

    results: list[tuple[Path, PluginTag]] = []
    for child in sorted(addons_dir.iterdir()):
        if not child.is_dir():
            continue
        tag = read_plugin_tag(child)
        if tag:
            results.append((child, tag))
    return results
