"""
Godot Asset Store API 客户端协议, 定义 StoreClient 的依赖注入接口.

Godot Asset Store API client protocol. Define the dependency-injection
interface of StoreClient for swappable implementations and unit tests.

----

Note:
    - StoreProtocol: Store 客户端依赖注入接口 / Store client injection interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from gdpm.models.plugin import Plugin, PluginDetail


class StoreProtocol(Protocol):
    """
    Store 客户端依赖注入接口, 约定 StoreClient 等实现方提供的能力,
    便于在测试中替换为假实现.

    Store client injection interface. Describe the capabilities of
    implementations such as StoreClient, making it easy to swap in fakes
    during testing.
    """

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        sort: str = "relevance",
    ) -> list[Plugin]:
        """
        搜索插件.

        Search plugins.

        ----

        Args:
            query: 搜索关键词 / Search keyword.
            limit: 返回数量上限 / Maximum number of results.
            sort: 排序方式, 如 relevance / Sort order, e.g. relevance.

        Returns:
            匹配的插件列表 / List of matching plugins.
        """
        ...

    async def get_plugin(self, publisher: str, slug: str) -> PluginDetail:
        """
        获取插件详情.

        Get plugin details.

        ----

        Args:
            publisher: 发布者 slug / Publisher slug.
            slug: 插件 slug / Plugin slug.

        Returns:
            插件详情 / Plugin details.
        """
        ...

    async def get_versions(self, publisher: str, slug: str) -> list[dict[str, str]]:
        """
        获取插件的版本列表.

        List plugin releases.

        ----

        Args:
            publisher: 发布者 slug / Publisher slug.
            slug: 插件 slug / Plugin slug.

        Returns:
            版本信息字典列表 / List of release info dicts.
        """
        ...

    async def download(
        self, publisher: str, slug: str, version: str, dest: Path
    ) -> Path:
        """
        下载插件 zip 包.

        Download the plugin zip archive.

        ----

        Args:
            publisher: 发布者 slug / Publisher slug.
            slug: 插件 slug / Plugin slug.
            version: 目标版本号 / Target version.
            dest: 保存目录 / Destination directory.

        Returns:
            zip 文件路径 / Path of the saved zip file.
        """
        ...
