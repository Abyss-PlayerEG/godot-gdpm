"""
缓存协议

- 定义缓存实现的依赖注入接口, 便于替换实现和编写单元测试.

----

Notes
----
- CacheProtocol: 缓存依赖注入接口.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class CacheProtocol(Protocol):
    """
    缓存依赖注入接口

    约定 FileCache 等实现方提供的键值式文件缓存能力.
    """

    def get(self, key: str) -> Path | None:
        """
        获取缓存文件.

        按缓存键查找缓存文件, 不存在则返回 None.

        ----

        Parameters
        ----
        key : str
            缓存键.

        Returns
        ----
        Path | None
            缓存文件路径, 不存在则返回 None.
        """
        ...

    def put(self, key: str, source: Path) -> Path:
        """
        写入缓存.

        复制源文件到缓存中的目标路径.

        ----

        Parameters
        ----
        key : str
            缓存键.
        source : Path
            待复制的源文件.

        Returns
        ----
        Path
            缓存中的目标路径.
        """
        ...

    def has(self, key: str) -> bool:
        """
        判断缓存是否存在.

        按缓存键检查缓存文件是否存在.

        ----

        Parameters
        ----
        key : str
            缓存键.

        Returns
        ----
        bool
            存在则为 True.
        """
        ...

    def clean(self) -> None:
        """清空缓存."""
        ...

    def size(self) -> int:
        """
        缓存占用的字节数.

        统计缓存文件总大小.

        ----

        Returns
        ----
        int
            缓存文件总大小.
        """
        ...
