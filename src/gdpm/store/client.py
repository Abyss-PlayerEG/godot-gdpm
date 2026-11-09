"""
Godot Asset Store API 客户端

- 通过 httpx 异步访问 Asset Store, 负责插件搜索, 详情, 版本查询与下载.

----

Notes
----
- DEFAULT_BASE_URL: Asset Store API 默认地址.
- ProgressCallback: 下载进度回调类型.
- StoreClient: REST API 异步客户端.
"""

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

# 下载进度回调: (已下载字节数, 总字节数, 速度 B/s).
ProgressCallback = Callable[[int, int, float], None]


class StoreClient:
    """
    Godot Asset Store REST API 异步客户端

    基于 httpx.AsyncClient, 提供搜索, 详情, 版本与流式下载接口.

    ----

    Attributes
    ----
    _base_url : str
        API 基础地址, 末尾不含斜杠.
    _client : httpx.AsyncClient
        底层 httpx 异步 HTTP 客户端.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        """
        初始化客户端.

        创建底层 httpx 异步 HTTP 客户端.

        ----

        Parameters
        ----
        base_url : str, optional
            API 基础地址, 末尾斜杠会被去除.
        """
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
        )

    async def close(self) -> None:
        """关闭底层 HTTP 客户端."""
        await self._client.aclose()

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        sort: str = "relevance",
        include_projects: bool = False,
    ) -> list[Plugin]:
        """
        搜索插件.

        调用 GET /search/query/ 检索资产, 默认只返回插件类型.

        ----

        Parameters
        ----
        query : str
            搜索关键词.
        limit : int, optional
            返回数量上限.
        sort : str, optional
            排序方式, 如 relevance.
        include_projects : bool, optional
            是否包含项目类型资产.

        Returns
        ----
        list[Plugin]
            解析后的插件列表.

        Raises
        ----
        httpx.HTTPError
            请求失败或响应状态码非 2xx.
        """
        params: dict[str, Any] = {
            "query": query,
            "sort": sort,
            "batch_size": limit,
        }
        if not include_projects:
            # type=0 只返回插件类型, 过滤掉项目模板.
            params["type"] = 0

        resp = await self._client.get("/search/query/", params=params)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        hits = data.get("hits", [])
        return [parse_search_hit(hit) for hit in hits]

    async def get_plugin(self, publisher: str, slug: str) -> PluginDetail:
        """
        获取插件详情.

        调用 GET /assets/{publisher}/{slug}/, 并用发布列表补全版本信息.

        ----

        Parameters
        ----
        publisher : str
            发布者 slug.
        slug : str
            插件 slug.

        Returns
        ----
        PluginDetail
            插件详情.

        Raises
        ----
        httpx.HTTPError
            请求失败或响应状态码非 2xx.
        """
        resp = await self._client.get(f"/assets/{publisher}/{slug}/")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        detail = parse_asset_detail(data)

        releases = await self.get_versions(publisher, slug)
        if releases:
            latest = releases[0]
            # 用最新 3 个发布补全版本与下载信息.
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
        """
        获取插件的版本列表.

        调用 GET /releases/{publisher}/{slug}/.

        ----

        Parameters
        ----
        publisher : str
            发布者 slug.
        slug : str
            插件 slug.

        Returns
        ----
        list[dict[str, str]]
            版本信息字典列表.

        Raises
        ----
        httpx.HTTPError
            请求失败或响应状态码非 2xx.
        """
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
        """
        下载插件 zip 包.

        按版本号匹配发布, 找不到时回退到最新发布.

        ----

        Parameters
        ----
        publisher : str
            发布者 slug.
        slug : str
            插件 slug.
        version : str
            目标版本号.
        dest : Path
            保存目录.
        on_progress : ProgressCallback | None, optional
            进度回调 (已下载, 总量, 速度 B/s).

        Returns
        ----
        Path
            zip 文件路径.

        Raises
        ----
        ValueError
            找不到发布记录或下载地址.
        httpx.HTTPError
            下载失败或响应状态码非 2xx.
        """
        releases = await self.get_versions(publisher, slug)
        target = None
        for r in releases:
            if r.get("version") == version:
                target = r
                break

        # 未找到指定版本时回退到最新发布.
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

        # 流式分块写入, 边下载边计算速度并回调进度.
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
