"""
Asset Store API 响应解析器

- 将 API 返回的原始 JSON 转换为内部数据模型.

----

Notes
----
- parse_search_hit: 搜索命中项转 Plugin.
- parse_asset_detail: 资产详情转 PluginDetail.
- parse_release: 发布记录规范化为字符串字典.
"""

from __future__ import annotations

from typing import Any

from gdpm.models.plugin import Plugin, PluginDetail


def parse_search_hit(hit: dict[str, Any]) -> Plugin:
    """
    将搜索命中项解析为 Plugin.

    命中项可能直接是资产, 也可能嵌套在 asset 字段中.

    ----

    Parameters
    ----
    hit : dict[str, Any]
        API 返回的搜索命中项.

    Returns
    ----
    Plugin
        解析后的插件模型.
    """
    # 命中项可能直接是资产或嵌套在 asset 字段.
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
    """
    将资产详情解析为 PluginDetail.

    版本相关字段留空, 由调用方按需补充.

    ----

    Parameters
    ----
    data : dict[str, Any]
        API 返回的资产详情.

    Returns
    ----
    PluginDetail
        解析后的插件详情模型.
    """
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
    """
    将发布记录规范化为字符串字典.

    字段值统一转为字符串.

    ----

    Parameters
    ----
    data : dict[str, Any]
        API 返回的发布记录.

    Returns
    ----
    dict[str, str]
        含 id, version, stable, created, 版本范围和下载地址的字典.
    """
    return {
        "id": str(data.get("id", "")),
        "version": data.get("version", ""),
        "stable": str(data.get("stable", True)),
        "created": data.get("created", ""),
        "min_godot_version": str(data.get("min_godot_version", "")),
        "max_godot_version": str(data.get("max_godot_version", "")),
        "download_url": data.get("download_url", ""),
    }
