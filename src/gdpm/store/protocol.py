"""
Godot Asset Store API 客户端协议

- 定义 StoreClient 的依赖注入接口.

----

Notes
----
- StoreProtocol: Store 客户端依赖注入接口.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from gdpm.models.plugin import Plugin, PluginDetail


class StoreProtocol(Protocol):
    """
    Store 客户端依赖注入接口

    约定 StoreClient 等实现方提供的能力, 便于在测试中替换为假实现.
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

        按搜索关键词与排序方式返回匹配的插件列表.

        ----

        Parameters
        ----
        query : str
            搜索关键词.
        limit : int, optional
            返回数量上限.
        sort : str, optional
            排序方式, 如 relevance.

        Returns
        ----
        list[Plugin]
            匹配的插件列表.
        """
        ...

    async def get_plugin(self, publisher: str, slug: str) -> PluginDetail:
        """
        获取插件详情.

        按发布者 slug 和插件 slug 获取插件详情.

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
        """
        ...

    async def get_versions(self, publisher: str, slug: str) -> list[dict[str, str]]:
        """
        获取插件的版本列表.

        按发布者 slug 和插件 slug 获取版本信息字典列表.

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
        """
        ...

    async def download(
        self, publisher: str, slug: str, version: str, dest: Path
    ) -> Path:
        """
        下载插件 zip 包.

        按目标版本号下载插件 zip 包到保存目录.

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

        Returns
        ----
        Path
            zip 文件路径.
        """
        ...
