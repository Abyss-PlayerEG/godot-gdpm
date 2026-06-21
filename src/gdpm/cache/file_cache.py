"""File-system based cache implementation."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class FileCache:
    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir
        self._downloads = cache_dir / "downloads"
        self._downloads.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._downloads

    def get(self, key: str) -> Path | None:
        path = self._key_path(key)
        if path.exists():
            return path
        return None

    def put(self, key: str, source: Path) -> Path:
        dest = self._key_path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        return dest

    def has(self, key: str) -> bool:
        return self._key_path(key).exists()

    def clean(self) -> None:
        if self._dir.exists():
            shutil.rmtree(self._dir)
            self._dir.mkdir(parents=True, exist_ok=True)
            self._downloads.mkdir(parents=True, exist_ok=True)

    def size(self) -> int:
        if not self._dir.exists():
            return 0
        total = 0
        for f in self._dir.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total

    def _key_path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self._downloads / safe_key
