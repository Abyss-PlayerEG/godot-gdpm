"""
Godot Asset Store API 客户端协议, 定义 StoreClient 的依赖注入接口.

----

Note:
    - StoreProtocol: Store 客户端依赖注入接口.
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

        ----

        Args:
            query: 搜索关键词.
            limit: 返回数量上限.
            sort: 排序方式, 如 relevance.

        Returns:
            匹配的插件列表.
        """
        ...

    async def get_plugin(self, publisher: str, slug: str) -> PluginDetail:
        """
        获取插件详情.

        ----

        Args:
            publisher: 发布者 slug.
            slug: 插件 slug.

        Returns:
            插件详情.
        """
        ...

    async def get_versions(self, publisher: str, slug: str) -> list[dict[str, str]]:
        """
        获取插件的版本列表.

        ----

        Args:
            publisher: 发布者 slug.
            slug: 插件 slug.

        Returns:
            版本信息字典列表.
        """
        ...

    async def download(
        self, publisher: str, slug: str, version: str, dest: Path
    ) -> Path:
        """
        下载插件 zip 包.

        ----

        Args:
            publisher: 发布者 slug.
            slug: 插件 slug.
            version: 目标版本号.
            dest: 保存目录.

        Returns:
            zip 文件路径.
        """
        ...
