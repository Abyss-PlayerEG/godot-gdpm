"""API response parser."""

from __future__ import annotations

from typing import Any

from gdpm.models.plugin import Plugin, PluginDetail


def parse_search_hit(hit: dict[str, Any]) -> Plugin:
    asset = hit.get("asset", hit)
    publisher_data = asset.get("publisher", {})
    tags_data = asset.get("tags", [])

    tags = [
        t.get("display_name", t.get("name", ""))
        for t in tags_data
        if isinstance(t, dict)
    ]
    return Plugin(
        slug=asset.get("slug", ""),
        name=asset.get("name", ""),
        description=asset.get("description", ""),
        author=publisher_data.get("name", ""),
        publisher_slug=publisher_data.get("slug", ""),
        license=asset.get("license_type", ""),
        store_url=asset.get("store_url", ""),
        tags=[t for t in tags if t],
        stars=asset.get("reviews_score", 0),
    )


def parse_asset_detail(data: dict[str, Any]) -> PluginDetail:
    publisher_data = data.get("publisher", {})
    tags_data = data.get("tags", [])

    tags = [
        t.get("display_name", t.get("name", ""))
        for t in tags_data
        if isinstance(t, dict)
    ]

    return PluginDetail(
        slug=data.get("slug", ""),
        name=data.get("name", ""),
        description=data.get("description", ""),
        author=publisher_data.get("name", ""),
        publisher_slug=publisher_data.get("slug", ""),
        license=data.get("license_type", ""),
        tags=[t for t in tags if t],
        stars=data.get("reviews_score", 0),
        homepage=data.get("store_url", ""),
        repository="",
        godot_versions=[],
        latest_version="",
        download_url="",
    )


def parse_release(data: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(data.get("id", "")),
        "version": data.get("version", ""),
        "stable": str(data.get("stable", True)),
        "created": data.get("created", ""),
        "min_godot_version": str(data.get("min_godot_version", "")),
        "max_godot_version": str(data.get("max_godot_version", "")),
        "download_url": data.get("download_url", ""),
    }
