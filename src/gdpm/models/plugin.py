"""Plugin data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Plugin:
    slug: str
    name: str
    description: str
    author: str
    publisher_slug: str
    license: str
    store_url: str = ""
    tags: list[str] = field(default_factory=list)
    stars: int = 0


@dataclass(frozen=True)
class PluginDetail(Plugin):
    homepage: str = ""
    repository: str = ""
    godot_versions: list[str] = field(default_factory=list)
    latest_version: str = ""
    download_url: str = ""
