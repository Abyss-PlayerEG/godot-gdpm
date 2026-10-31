"""
基于文件系统的缓存实现.

File-system based cache implementation.

----

Note:
    - 缓存目录结构 / Cache directory layout:
        <cache_dir>/downloads/<letter>/<publisher>_<slug>@<version>
    - letter: 发布者首字母小写, 用于目录分片 /
        Lowercased first letter of the publisher, used for sharding.
    - 键中的斜杠会替换为下划线 / Slashes in keys are replaced with "_".
    - FileCache: 满足 CacheProtocol 的文件缓存实现 /
        File cache implementation satisfying CacheProtocol.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class FileCache:
    """
    本地文件缓存, 将 zip 文件按发布者首字母分片存放, 满足 CacheProtocol.

    Local file cache. Store zip files sharded by the publisher's first
    letter, satisfying CacheProtocol.

    ----

    Attributes:
        path: downloads 分片根目录 / Root directory of the letter shards.
    """

    def __init__(self, cache_dir: Path) -> None:
        """
        初始化缓存目录.

        Initialize the cache directory.

        ----

        Args:
            cache_dir: 缓存根目录, 自动创建 downloads 子目录 /
                Cache root directory; the downloads subdir is created
                automatically.
        """
        self._dir = cache_dir
        self._downloads = cache_dir / "downloads"
        self._downloads.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        """downloads 分片根目录 / Root directory of the letter shards."""
        return self._downloads

    def get(self, key: str) -> Path | None:
        """
        获取缓存文件.

        Get a cached file.

        ----

        Args:
            key: 缓存键, 如 "publisher/slug@version" /
                Cache key such as "publisher/slug@version".

        Returns:
            缓存文件路径, 不存在则返回 None / Cached file path, or None when missing.
        """
        path = self._key_path(key)
        if path.exists():
            return path
        return None

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
        dest = self._key_path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        return dest

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
        return self._key_path(key).exists()

    def clean(self) -> None:
        """清空缓存并重建目录结构 / Clear the cache and rebuild the layout."""
        if self._dir.exists():
            shutil.rmtree(self._dir)
            self._dir.mkdir(parents=True, exist_ok=True)
            self._downloads.mkdir(parents=True, exist_ok=True)

    def size(self) -> int:
        """
        统计缓存占用的字节数.

        Compute the total cache size in bytes.

        Returns:
            缓存目录下所有文件的大小之和 /
                Sum of the sizes of all files in the cache directory.
        """
        if not self._dir.exists():
            return 0
        total = 0
        for f in self._dir.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total

    def _letter_dir(self, key: str) -> Path:
        """
        根据键计算分片目录.

        Compute the shard directory for a key.

        ----

        Args:
            key: 缓存键 / Cache key.

        Returns:
            发布者首字母对应的分片目录 /
                Shard directory named after the publisher's first letter.
        """
        # 取发布者部分作为分片依据, 无发布者时使用 "x" /
        # Shard by the publisher part, "x" when there is none.
        publisher = key.split("/")[0] if "/" in key else key
        letter = publisher[0].lower() if publisher else "x"
        return self._downloads / letter

    def _key_path(self, key: str) -> Path:
        """
        将缓存键映射为文件路径.

        Map a cache key to a file path.

        ----

        Args:
            key: 缓存键 / Cache key.

        Returns:
            分片目录下的安全文件路径 / Safe file path inside the shard directory.
        """
        # 替换斜杠, 防止键被解析为子目录 /
        # Replace slashes so keys are not treated as subdirectories.
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self._letter_dir(key) / safe_key
