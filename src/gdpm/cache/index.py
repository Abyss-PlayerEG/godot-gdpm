"""
缓存索引管理

- 支持快速查找缓存.
- 索引按首字母拆分为多个 index.json, 与 FileCache 的分片目录一致.

----

Notes
----
- CacheEntry: 单条缓存记录.
- CacheIndex: 索引的读写与查询.
- make_cache_key: 生成缓存键.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

INDEX_FILE = "index.json"


@dataclass
class CacheEntry:
    """
    单条缓存索引记录

    记录缓存文件名与下载时间.

    ----

    Attributes
    ----
    file : str
        缓存文件名.
    downloaded_at : str
        下载时间 (ISO 格式).
    """

    file: str
    downloaded_at: str


class CacheIndex:
    """
    缓存索引管理

    按首字母拆分缓存索引文件, 每个分片目录下保存 index.json,
    已加载的索引缓存在内存中.

    ----

    Attributes
    ----
    _downloads : Path
        downloads 分片根目录.
    _cache : dict[str, dict[str, CacheEntry]]
        字母到索引的内存缓存.
    """

    def __init__(self, downloads_dir: Path) -> None:
        """
        初始化索引管理器.

        已加载的索引缓存在内存中.

        ----

        Parameters
        ----
        downloads_dir : Path
            downloads 分片根目录.
        """
        self._downloads = downloads_dir
        self._cache: dict[str, dict[str, CacheEntry]] = {}

    def _get_index_path(self, letter: str) -> Path:
        """
        获取分片索引文件路径.

        按分片字母拼出 index.json 路径.

        ----

        Parameters
        ----
        letter : str
            分片字母.

        Returns
        ----
        Path
            分片目录下的 index.json 路径.
        """
        return self._downloads / letter / INDEX_FILE

    def _load_letter(self, letter: str) -> dict[str, CacheEntry]:
        """
        加载分片索引.

        优先使用内存缓存.

        ----

        Parameters
        ----
        letter : str
            分片字母.

        Returns
        ----
        dict[str, CacheEntry]
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
                    # 兼容旧索引: 忽略已移除的 hash 字段
                    entry.pop("hash", None)
                    data[key] = CacheEntry(**entry)
            except json.JSONDecodeError, TypeError:
                # 索引损坏时按空索引处理.
                data = {}

        self._cache[letter] = data
        return data

    def _save_letter(self, letter: str) -> None:
        """
        将分片索引写回磁盘.

        写入分片目录下的 index.json.

        ----

        Parameters
        ----
        letter : str
            分片字母.
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

        取缓存键的发布者首字母小写作为分片字母.

        ----

        Parameters
        ----
        key : str
            缓存键.

        Returns
        ----
        str
            发布者首字母小写, 无发布者时为 "x".
        """
        publisher = key.split("/")[0] if "/" in key else key
        return publisher[0].lower() if publisher else "x"

    def get(self, key: str) -> CacheEntry | None:
        """
        查询缓存记录.

        按缓存键查询, 不存在则返回 None.

        ----

        Parameters
        ----
        key : str
            缓存键.

        Returns
        ----
        CacheEntry | None
            缓存记录, 不存在则返回 None.
        """
        letter = self._letter_for_key(key)
        data = self._load_letter(letter)
        return data.get(key)

    def has(self, key: str) -> bool:
        """
        判断缓存记录是否存在.

        按缓存键检查记录是否存在.

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
        return self.get(key) is not None

    def put(
        self,
        key: str,
        file: str,
    ) -> CacheEntry:
        """
        写入或更新缓存记录.

        记录下载时间, 不计算文件哈希 (无消费方, 属无谓的全文件读取).

        ----

        Parameters
        ----
        key : str
            缓存键.
        file : str
            缓存文件名.

        Returns
        ----
        CacheEntry
            写入的缓存记录.
        """
        entry = CacheEntry(
            file=file,
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

        删除后同步保存分片索引.

        ----

        Parameters
        ----
        key : str
            缓存键.

        Returns
        ----
        bool
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
        按插件 slug 查找缓存记录.

        匹配 "slug@version" 形式的键或完全相等的键.

        ----

        Parameters
        ----
        slug : str
            插件 slug.

        Returns
        ----
        list[tuple[str, CacheEntry]]
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

        合并所有分片的索引.

        ----

        Returns
        ----
        dict[str, CacheEntry]
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

    发布者与 slug 用斜杠分隔, 与版本号用 @ 连接.

    ----

    Parameters
    ----
    publisher : str
        发布者 slug.
    slug : str
        插件 slug.
    version : str
        版本号.

    Returns
    ----
    str
        形如 "publisher/slug@version" 的缓存键.

    Examples
    ----
    >>> make_cache_key("rsubtil", "controller-icons", "v2.0.1")
        'rsubtil/controller-icons@v2.0.1'
    """
    return f"{publisher}/{slug}@{version}"
