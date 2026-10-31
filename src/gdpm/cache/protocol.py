"""
缓存协议, 定义缓存实现的依赖注入接口, 便于替换实现和编写单元测试.

Cache protocol. Define the dependency-injection interface of cache
implementations for swappable backends and unit tests.

----

Note:
    - CacheProtocol: 缓存依赖注入接口 / Cache dependency-injection interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class CacheProtocol(Protocol):
    """
    缓存依赖注入接口, 约定 FileCache 等实现方提供的键值式文件缓存能力.

    Cache dependency-injection interface. Describe the key-based file
    caching capabilities of implementations such as FileCache.
    """

    def get(self, key: str) -> Path | None:
        """
        获取缓存文件.

        Get a cached file.

        ----

        Args:
            key: 缓存键 / Cache key.

        Returns:
            缓存文件路径, 不存在则返回 None / Cached file path, or None when missing.
        """
        ...

    def put(self, key: str, source: Path) -> Path:
        """
        写入缓存.

        Store a file in the cache.

        ----

        Args:
            key: 缓存键 / Cache key.
            source: 待复制的源文件 / Source file to copy.

        Returns:
            缓存中的目标路径 / Destination path in the cache.
        """
        ...

    def has(self, key: str) -> bool:
        """
        判断缓存是否存在.

        Whether the cache entry exists.

        ----

        Args:
            key: 缓存键 / Cache key.

        Returns:
            存在则为 True / True when the entry exists.
        """
        ...

    def clean(self) -> None:
        """清空缓存 / Clear the cache."""
        ...

    def size(self) -> int:
        """
        缓存占用的字节数.

        Cache size in bytes.

        Returns:
            缓存文件总大小 / Total size of the cached files.
        """
        ...
