"""Godot Asset Store API client protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from gdpm.models.plugin import Plugin, PluginDetail


class StoreProtocol(Protocol):
    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        sort: str = "relevance",
    ) -> list[Plugin]: ...

    async def get_plugin(self, publisher: str, slug: str) -> PluginDetail: ...

    async def get_versions(self, publisher: str, slug: str) -> list[dict[str, str]]: ...

    async def download(
        self, publisher: str, slug: str, version: str, dest: Path
    ) -> Path: ...
