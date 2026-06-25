"""Plugin installer manager."""

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
    def __init__(
        self,
        addons_dir: Path,
        cache: FileCache,
        store: StoreClient | None = None,
    ) -> None:
        self._addons = addons_dir
        self._project_root = addons_dir.parent
        self._cache = cache
        self._index = CacheIndex(cache.path.parent)
        self._store = store or StoreClient()
        self._owns_store = store is None

    async def close(self) -> None:
        if self._owns_store:
            await self._store.close()

    async def download(
        self,
        publisher: str,
        slug: str,
        version: str = "",
        on_progress: ProgressCallback | None = None,
    ) -> tuple[Path, str]:
        # If no version specified, get latest from API
        if not version:
            releases = await self._store.get_versions(publisher, slug)
            if not releases:
                raise ValueError(f"No releases found for {publisher}/{slug}")
            ver = releases[0]["version"]
        else:
            ver = version.lstrip("v")
            if not ver.startswith("v"):
                ver = f"v{ver}"

        # Check cache index first
        cache_key = make_cache_key(publisher, slug, ver)
        entry = self._index.get(cache_key)

        if entry:
            cached_path = self._cache.path / entry.file
            if cached_path.exists():
                return cached_path, entry.version
            else:
                # File missing, clean stale index entry
                self._index.remove(cache_key)

        # Cache miss - need to download
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
        zip_path = await self._store.download(
            publisher,
            slug,
            ver,
            self._cache.path,
            on_progress=on_progress,
        )

        # Update cache index
        self._index.put(cache_key, zip_path.name, zip_path)

        return zip_path, ver

    def analyze(self, zip_path: Path) -> ZipAnalysis:
        return analyze_zip(zip_path)

    def extract_to_path(
        self, zip_path: Path, dest: Path, slug: str, publisher: str = ""
    ) -> None:
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
                tag_dest = dest / next(iter(root_dirs)) if len(root_dirs) == 1 else dest
            else:
                tag_dest = dest

            tag_path = tag_dest / TAG_FILENAME
            tag_path.write_text(source, encoding="utf-8")
            return {"dest": str(dest), "addon_dirs": []}

        if analysis.has_addons:
            extracted = extract_addon_from_zip(zip_path, self._addons, slug)
            if not extracted:
                raise ValueError(f"Plugin '{slug}' extraction failed.")
            for addon_dir in extracted:
                tag_path = self._addons / addon_dir / TAG_FILENAME
                tag_path.write_text(source, encoding="utf-8")
            return {"dest": str(self._addons), "addon_dirs": extracted}

        if len(analysis.asset_dirs or []) > 0:
            return {"dest": "", "addon_dirs": [], "has_assets": True}

        raise ValueError(
            f"Plugin '{slug}' is not an addon (no addons/ directory in zip). "
            "Use --path to specify a custom install path."
        )

    def write_tag(self, dest: Path, slug: str, publisher: str = "") -> None:
        source = f"store+{publisher}/{slug}" if publisher else f"store+{slug}"
        tag_path = dest / TAG_FILENAME
        tag_path.write_text(source, encoding="utf-8")

    def remove(self, slug: str) -> None:
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
        return len(self.find_addon_dirs(slug)) > 0
