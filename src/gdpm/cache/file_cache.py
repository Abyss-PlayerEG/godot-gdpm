"""
基于文件系统的缓存实现

- 将 zip 文件按发布者首字母分片存放.

----

Notes
----
- 缓存目录结构:
    <cache_dir>/downloads/<letter>/<publisher>_<slug>@<version>
- letter: 发布者首字母小写, 用于目录分片.
- 键中的斜杠会替换为下划线.
- FileCache: 满足 CacheProtocol 的文件缓存实现.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class FileCache:
    """
    本地文件缓存

    将 zip 文件按发布者首字母分片存放, 满足 CacheProtocol.

    ----

    Attributes
    ----
    path : Path
        downloads 分片根目录.
    """

    def __init__(self, cache_dir: Path) -> None:
        """
        初始化缓存目录.

        自动创建 downloads 子目录.

        ----

        Parameters
        ----
        cache_dir : Path
            缓存根目录.
        """
        self._dir = cache_dir
        self._downloads = cache_dir / "downloads"
        self._downloads.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        """downloads 分片根目录."""
        return self._downloads

    def get(self, key: str) -> Path | None:
        """
        获取缓存文件.

        缓存键形如 "publisher/slug@version".

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
        path = self._key_path(key)
        if path.exists():
            return path
        return None

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
        dest = self._key_path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        return dest

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
        return self._key_path(key).exists()

    def clean(self) -> None:
        """清空缓存并重建目录结构."""
        if self._dir.exists():
            shutil.rmtree(self._dir)
            self._dir.mkdir(parents=True, exist_ok=True)
            self._downloads.mkdir(parents=True, exist_ok=True)

    def size(self) -> int:
        """
        统计缓存占用的字节数.

        累加缓存目录下所有文件的大小.

        ----

        Returns
        ----
        int
            缓存目录下所有文件的大小之和.
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

        按缓存键的发布者首字母定位分片目录.

        ----

        Parameters
        ----
        key : str
            缓存键.

        Returns
        ----
        Path
            发布者首字母对应的分片目录.
        """
        # 取发布者部分作为分片依据, 无发布者时使用 "x".
        publisher = key.split("/")[0] if "/" in key else key
        letter = publisher[0].lower() if publisher else "x"
        return self._downloads / letter

    def _key_path(self, key: str) -> Path:
        """
        将缓存键映射为文件路径.

        键中的斜杠会替换为下划线.

        ----

        Parameters
        ----
        key : str
            缓存键.

        Returns
        ----
        Path
            分片目录下的安全文件路径.
        """
        # 替换斜杠, 防止键被解析为子目录.
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self._letter_dir(key) / safe_key
