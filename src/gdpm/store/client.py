"""Godot Asset Store API client."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import httpx

from gdpm.models.plugin import Plugin, PluginDetail
from gdpm.store.parser import parse_asset_detail, parse_release, parse_search_hit

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_BASE_URL = "https://store.godotengine.org/api/v1"

ProgressCallback = Callable[[int, int, float], None]


class StoreClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        sort: str = "relevance",
        include_projects: bool = False,
    ) -> list[Plugin]:
        params: dict[str, Any] = {
            "query": query,
            "sort": sort,
            "batch_size": limit,
        }
        if not include_projects:
            params["type"] = 0

        resp = await self._client.get("/search/query/", params=params)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        hits = data.get("hits", [])
        return [parse_search_hit(hit) for hit in hits]

    async def get_plugin(self, publisher: str, slug: str) -> PluginDetail:
        resp = await self._client.get(f"/assets/{publisher}/{slug}/")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        detail = parse_asset_detail(data)

        releases = await self.get_versions(publisher, slug)
        if releases:
            latest = releases[0]
            detail = PluginDetail(
                slug=detail.slug,
                name=detail.name,
                description=detail.description,
                author=detail.author,
                publisher_slug=detail.publisher_slug,
                license=detail.license,
                tags=detail.tags,
                stars=detail.stars,
                homepage=detail.homepage,
                repository=detail.repository,
                godot_versions=[r.get("min_godot_version", "") for r in releases[:3]],
                latest_version=latest.get("version", ""),
                download_url=latest.get("download_url", ""),
            )

        return detail

    async def get_versions(self, publisher: str, slug: str) -> list[dict[str, str]]:
        resp = await self._client.get(f"/releases/{publisher}/{slug}/")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return [parse_release(r) for r in data]

    async def download(
        self,
        publisher: str,
        slug: str,
        version: str,
        dest: Path,
        on_progress: ProgressCallback | None = None,
    ) -> Path:
        releases = await self.get_versions(publisher, slug)
        target = None
        for r in releases:
            if r.get("version") == version:
                target = r
                break

        if target is None and releases:
            target = releases[0]

        if target is None:
            raise ValueError(f"No releases found for {publisher}/{slug}")

        download_url = target.get("download_url", "")
        if not download_url:
            raise ValueError(f"No download URL for {publisher}/{slug} v{version}")

        dest.mkdir(parents=True, exist_ok=True)
        zip_path = dest / f"{slug}-{version}.zip"

        start_time = time.monotonic()
        downloaded = 0

        async with self._client.stream("GET", download_url) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            with open(zip_path, "wb") as f:
                async for chunk in resp.aiter_bytes(8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress:
                        elapsed = time.monotonic() - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        on_progress(downloaded, total, speed)

        return zip_path
