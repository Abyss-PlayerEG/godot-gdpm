"""
插件安装管理, 负责从缓存或 Store 下载插件并安装到 addons 目录.

----

Note:
    - PluginManager: 插件安装管理器.
    - TAG_FILENAME: 插件标记文件名.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Any

from gdpm.cache.index import CacheIndex, make_cache_key
from gdpm.store.client import StoreClient
from gdpm.utils.zip import (
    ZipAnalysis,
    analyze_zip,
    extract_addon_from_zip,
    extract_full_zip,
)

if TYPE_CHECKING:
    from pathlib import Path

    from gdpm.cache.file_cache import FileCache
    from gdpm.store.client import ProgressCallback

TAG_FILENAME = "tag.gdpm"


class PluginManager:
    """
    插件安装管理器, 管理插件的下载, 解压安装, 标记与卸载, 并维护下载缓存索引.

    ----

    Attributes:
        _addons: addons 目录路径.
        _project_root: 项目根目录.
        _cache: 文件缓存.
        _index: 缓存索引.
        _store: Asset Store 客户端.
        _owns_store: 客户端是否由本对象创建.
    """

    def __init__(
        self,
        addons_dir: Path,
        cache: FileCache,
        store: StoreClient | None = None,
    ) -> None:
        """
        初始化插件管理器.

        ----

        Args:
            addons_dir: addons 目录路径.
            cache: 文件缓存实例.
            store: Store 客户端, 为空时自动创建.
        """
        self._addons = addons_dir
        self._project_root = addons_dir.parent
        self._cache = cache
        self._index = CacheIndex(cache.path)
        self._store = store or StoreClient()
        self._owns_store = store is None

    async def close(self) -> None:
        """
        关闭内部创建的 Store 客户端, 仅在客户端由本对象创建时才执行关闭.
        """
        if self._owns_store:
            await self._store.close()

    async def download(
        self,
        publisher: str,
        slug: str,
        version: str = "",
        on_progress: ProgressCallback | None = None,
        use_cache: bool = True,
    ) -> tuple[Path, str]:
        """
        下载插件压缩包, 先查询缓存索引, 未命中时从 Store 下载并更新索引.

        ----

        Args:
            publisher: 发布者 slug.
            slug: 插件 slug.
            version: 版本号, 为空时取最新版本.
            on_progress: 进度回调.
            use_cache: 是否使用本地缓存.

        Returns:
            (压缩包路径, 版本号) 元组.

        Raises:
            ValueError: 找不到发布版本或指定版本.
        """
        # 未指定版本时取 API 最新版本
        if not version:
            releases = await self._store.get_versions(publisher, slug)
            if not releases:
                raise ValueError(f"No releases found for {publisher}/{slug}")
            ver = releases[0]["version"]
        else:
            ver = version.lstrip("v")
            if not ver.startswith("v"):
                ver = f"v{ver}"

        # 先查缓存索引
        cache_key = make_cache_key(publisher, slug, ver)
        if use_cache:
            entry = self._index.get(cache_key)

            if entry:
                letter = publisher[0].lower() if publisher else "x"
                cached_path = self._cache.path / letter / entry.file
                if cached_path.exists():
                    return cached_path, ver
                else:
                    # 文件缺失, 清理过期索引项
                    self._index.remove(cache_key)

        # 缓存未命中, 需要下载
        if version:
            releases = await self._store.get_versions(publisher, slug)
            normalized = ver.lstrip("v")
            target = next(
                (r for r in releases if r["version"].lstrip("v") == normalized),
                None,
            )
            if target is None:
                raise ValueError(f"Version {version} not found for {publisher}/{slug}")
        else:
            releases = await self._store.get_versions(publisher, slug)
            if not releases:
                raise ValueError(f"No releases found for {publisher}/{slug}")
            target = releases[0]

        ver = target["version"]
        letter = publisher[0].lower() if publisher else "x"
        dest_dir = self._cache.path / letter
        zip_path = await self._store.download(
            publisher,
            slug,
            ver,
            dest_dir,
            on_progress=on_progress,
        )

        # 更新缓存索引
        self._index.put(cache_key, zip_path.name, zip_path)

        return zip_path, ver

    def analyze(self, zip_path: Path) -> ZipAnalysis:
        """
        分析压缩包结构.

        ----

        Args:
            zip_path: 压缩包路径.

        Returns:
            压缩包结构分析结果.
        """
        return analyze_zip(zip_path)

    def extract_to_path(
        self, zip_path: Path, dest: Path, slug: str, publisher: str = ""
    ) -> None:
        """
        将压缩包完整解压到指定路径并写入标记文件.

        ----

        Args:
            zip_path: 压缩包路径.
            dest: 解压目标目录.
            slug: 插件 slug.
            publisher: 发布者 slug.
        """
        dest.mkdir(parents=True, exist_ok=True)
        extract_full_zip(zip_path, dest)

        source = f"store+{publisher}/{slug}" if publisher else f"store+{slug}"
        tag_path = dest / TAG_FILENAME
        tag_path.write_text(source, encoding="utf-8")

    def install_from_zip(
        self,
        zip_path: Path,
        slug: str,
        publisher: str = "",
        dest_path: str = "",
    ) -> dict[str, Any]:
        """
        从压缩包安装插件, 优先按 addons/ 结构解压, 否则按自定义路径或
        资产目录处理.

        ----

        Args:
            zip_path: 压缩包路径.
            slug: 插件 slug.
            publisher: 发布者 slug.
            dest_path: 自定义安装路径.

        Returns:
            包含安装目标与 addon 目录的字典.

        Raises:
            ValueError: 解压失败或不是合法插件包.
        """
        analysis = analyze_zip(zip_path)
        source = f"store+{publisher}/{slug}" if publisher else f"store+{slug}"

        if dest_path:
            dest = self._project_root / dest_path
            dest.mkdir(parents=True, exist_ok=True)
            extract_full_zip(zip_path, dest)

            if dest_path.endswith("/"):
                root_dirs: set[str] = set()
                for item in dest.iterdir():
                    if item.is_dir():
                        root_dirs.add(item.name)
                # 仅一个根目录时标记写入其中
                tag_dest = dest / next(iter(root_dirs)) if len(root_dirs) == 1 else dest
            else:
                tag_dest = dest

            tag_path = tag_dest / TAG_FILENAME
            tag_path.write_text(source, encoding="utf-8")
            return {"dest": str(dest), "addon_dirs": []}

        # 含 addons/ 结构, 安装到 addons 目录
        if analysis.has_addons:
            extracted = extract_addon_from_zip(zip_path, self._addons, slug)
            if not extracted:
                raise ValueError(f"Plugin '{slug}' extraction failed.")
            for addon_dir in extracted:
                tag_path = self._addons / addon_dir / TAG_FILENAME
                tag_path.write_text(source, encoding="utf-8")
            return {"dest": str(self._addons), "addon_dirs": extracted}

        # 纯资产包, 交由调用方处理
        if len(analysis.asset_dirs or []) > 0:
            return {"dest": "", "addon_dirs": [], "has_assets": True}

        raise ValueError(
            f"Plugin '{slug}' is not an addon (no addons/ directory in zip). "
            "Use --path to specify a custom install path."
        )

    def write_tag(self, dest: Path, slug: str, publisher: str = "") -> None:
        """
        向目标目录写入插件来源标记.

        ----

        Args:
            dest: 插件目录.
            slug: 插件 slug.
            publisher: 发布者 slug.
        """
        source = f"store+{publisher}/{slug}" if publisher else f"store+{slug}"
        tag_path = dest / TAG_FILENAME
        tag_path.write_text(source, encoding="utf-8")

    def remove(self, slug: str) -> None:
        """
        删除属于指定插件的目录, 通过标记文件匹配插件归属.

        ----

        Args:
            slug: 插件 slug.
        """
        if not self._addons.exists():
            return

        for child in self._addons.iterdir():
            if not child.is_dir():
                continue
            tag_path = child / TAG_FILENAME
            if tag_path.exists():
                tag_content = tag_path.read_text(encoding="utf-8").strip()
                if tag_content.endswith(f"/{slug}"):
                    shutil.rmtree(child)

    def find_addon_dirs(self, slug: str) -> list[str]:
        """
        查找属于指定插件的 addon 目录名.

        ----

        Args:
            slug: 插件 slug.

        Returns:
            addon 目录名列表.
        """
        if not self._addons.exists():
            return []

        dirs: list[str] = []
        for child in self._addons.iterdir():
            if not child.is_dir():
                continue
            tag_path = child / TAG_FILENAME
            if tag_path.exists():
                tag_content = tag_path.read_text(encoding="utf-8").strip()
                if tag_content.endswith(f"/{slug}"):
                    dirs.append(child.name)
        return dirs

    def is_installed(self, slug: str) -> bool:
        """
        判断插件是否已安装.

        ----

        Args:
            slug: 插件 slug.

        Returns:
            已安装返回 True.
        """
        return len(self.find_addon_dirs(slug)) > 0
