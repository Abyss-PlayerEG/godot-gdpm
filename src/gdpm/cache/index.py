"""
缓存索引管理, 支持快速查找缓存, 索引按首字母拆分为多个 index.json,
与 FileCache 的分片目录一致.

----

Note:
    - CacheEntry: 单条缓存记录.
    - CacheIndex: 索引的读写与查询.
    - make_cache_key: 生成缓存键.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from gdpm.utils.checksum import sha256_file

if TYPE_CHECKING:
    from pathlib import Path

INDEX_FILE = "index.json"


@dataclass
class CacheEntry:
    """
    单条缓存索引记录.

    ----

    Attributes:
        file: 缓存文件名.
        hash: zip 文件的 SHA256 校验和.
        downloaded_at: 下载时间 (ISO 格式).
    """

    file: str
    hash: str
    downloaded_at: str


class CacheIndex:
    """
    管理按首字母拆分的缓存索引文件, 每个分片目录下保存 index.json,
    已加载的索引缓存在内存中.

    ----

    Attributes:
        _downloads: downloads 分片根目录.
        _cache: 字母到索引的内存缓存.
    """

    def __init__(self, downloads_dir: Path) -> None:
        """
        初始化索引管理器.

        ----

        Args:
            downloads_dir: downloads 分片根目录.
        """
        self._downloads = downloads_dir
        self._cache: dict[str, dict[str, CacheEntry]] = {}

    def _get_index_path(self, letter: str) -> Path:
        """
        获取分片索引文件路径.

        ----

        Args:
            letter: 分片字母.

        Returns:
            分片目录下的 index.json 路径.
        """
        return self._downloads / letter / INDEX_FILE

    def _load_letter(self, letter: str) -> dict[str, CacheEntry]:
        """
        加载分片索引, 优先使用内存缓存.

        ----

        Args:
            letter: 分片字母.

        Returns:
            该分片的键到记录映射.
        """
        if letter in self._cache:
            return self._cache[letter]

        path = self._get_index_path(letter)
        data: dict[str, CacheEntry] = {}

        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                for key, entry in raw.items():
                    data[key] = CacheEntry(**entry)
            except json.JSONDecodeError, TypeError:
                # 索引损坏时按空索引处理.
                data = {}

        self._cache[letter] = data
        return data

    def _save_letter(self, letter: str) -> None:
        """
        将分片索引写回磁盘.

        ----

        Args:
            letter: 分片字母.
        """
        if letter not in self._cache:
            return

        path = self._get_index_path(letter)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = {k: vars(v) for k, v in self._cache[letter].items()}
        path.write_text(
            json.dumps(raw, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _letter_for_key(self, key: str) -> str:
        """
        由缓存键推导分片字母.

        ----

        Args:
            key: 缓存键.

        Returns:
            发布者首字母小写, 无发布者时为 "x".
        """
        publisher = key.split("/")[0] if "/" in key else key
        return publisher[0].lower() if publisher else "x"

    def get(self, key: str) -> CacheEntry | None:
        """
        查询缓存记录.

        ----

        Args:
            key: 缓存键.

        Returns:
            缓存记录, 不存在则返回 None.
        """
        letter = self._letter_for_key(key)
        data = self._load_letter(letter)
        return data.get(key)

    def has(self, key: str) -> bool:
        """
        判断缓存记录是否存在.

        ----

        Args:
            key: 缓存键.

        Returns:
            存在则为 True.
        """
        return self.get(key) is not None

    def put(
        self,
        key: str,
        file: str,
        zip_path: Path,
    ) -> CacheEntry:
        """
        写入或更新缓存记录.

        ----

        Args:
            key: 缓存键.
            file: 缓存文件名.
            zip_path: 用于计算校验和的 zip 文件.

        Returns:
            写入的缓存记录.
        """
        hash_val = sha256_file(zip_path) if zip_path.exists() else ""
        entry = CacheEntry(
            file=file,
            hash=hash_val,
            downloaded_at=datetime.now(UTC).isoformat(),
        )
        letter = self._letter_for_key(key)
        data = self._load_letter(letter)
        data[key] = entry
        self._save_letter(letter)
        return entry

    def remove(self, key: str) -> bool:
        """
        删除缓存记录.

        ----

        Args:
            key: 缓存键.

        Returns:
            是否删除了记录.
        """
        letter = self._letter_for_key(key)
        data = self._load_letter(letter)
        if key in data:
            del data[key]
            self._save_letter(letter)
            return True
        return False

    def find_by_slug(self, slug: str) -> list[tuple[str, CacheEntry]]:
        """
        按插件 slug 查找缓存记录, 匹配 "slug@version" 形式的键或完全相等的键.

        ----

        Args:
            slug: 插件 slug.

        Returns:
            命中的 (键, 记录) 列表.
        """
        results = []
        for letter_dir in self._downloads.iterdir():
            if not letter_dir.is_dir():
                continue
            data = self._load_letter(letter_dir.name)
            for key, entry in data.items():
                # 同一 slug 可能对应多个版本.
                if key.startswith(f"{slug}@") or key == slug:
                    results.append((key, entry))
        return results

    def list_all(self) -> dict[str, CacheEntry]:
        """
        列出全部缓存记录.

        Returns:
            合并所有分片后的键到记录映射.
        """
        result: dict[str, CacheEntry] = {}
        for letter_dir in self._downloads.iterdir():
            if not letter_dir.is_dir():
                continue
            data = self._load_letter(letter_dir.name)
            result.update(data)
        return result


def make_cache_key(publisher: str, slug: str, version: str) -> str:
    """
    由发布者, slug 和版本号生成缓存键.

    ----

    example:
        >>> make_cache_key("rsubtil", "controller-icons", "v2.0.1")
        'rsubtil/controller-icons@v2.0.1'

    ----

    Args:
        publisher: 发布者 slug.
        slug: 插件 slug.
        version: 版本号.

    Returns:
        形如 "publisher/slug@version" 的缓存键.
    """
    return f"{publisher}/{slug}@{version}"
