"""Plugin installer manager."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Any

from gdpm.store.client import StoreClient
from gdpm.utils.checksum import sha256_file
from gdpm.utils.zip import extract_addon_from_zip

if TYPE_CHECKING:
    from pathlib import Path

    from gdpm.cache.file_cache import FileCache

TAG_FILENAME = "tag.gdpm"


class PluginManager:
    def __init__(
        self,
        addons_dir: Path,
        cache: FileCache,
        store: StoreClient | None = None,
    ) -> None:
        self._addons = addons_dir
        self._cache = cache
        self._store = store or StoreClient()
        self._owns_store = store is None

    async def close(self) -> None:
        if self._owns_store:
            await self._store.close()

    async def install(
        self,
        publisher: str,
        slug: str,
        version: str = "",
    ) -> dict[str, Any]:
        releases = await self._store.get_versions(publisher, slug)
        if not releases:
            raise ValueError(f"No releases found for {publisher}/{slug}")

        if version:
            normalized = version.lstrip("v")
            target = next(
                (r for r in releases if r["version"].lstrip("v") == normalized),
                None,
            )
            if target is None:
                raise ValueError(f"Version {version} not found for {publisher}/{slug}")
        else:
            target = releases[0]

        ver = target["version"]
        cache_key = f"{publisher}_{slug}_{ver}.zip"
        zip_path = self._cache.get(cache_key)

        if zip_path is None:
            zip_path = await self._store.download(
                publisher, slug, ver, self._cache.path
            )
            self._cache.put(cache_key, zip_path)

        extracted = extract_addon_from_zip(zip_path, self._addons, slug)
        if not extracted:
            raise ValueError(
                f"Plugin '{slug}' is not an addon (no addons/ directory in zip). "
                "It may be a project template."
            )

        source = f"store+{publisher}/{slug}"
        for addon_dir in extracted:
            tag_path = self._addons / addon_dir / TAG_FILENAME
            tag_path.write_text(source, encoding="utf-8")

        checksum = sha256_file(zip_path) if zip_path.exists() else ""

        return {
            "name": slug,
            "version": ver,
            "source": source,
            "checksum": checksum,
        }

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

    def installed_version(self, slug: str) -> str | None:
        cfg = self._addons / slug / "plugin.cfg"
        if not cfg.exists():
            return None
        try:
            import configparser

            parser = configparser.ConfigParser()
            parser.read(cfg)
            return parser.get("plugin", "version", fallback=None)
        except Exception:
            return None
