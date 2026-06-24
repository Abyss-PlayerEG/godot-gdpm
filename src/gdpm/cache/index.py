"""Cache index management for fast cache lookups."""

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
    file: str
    version: str
    hash: str
    downloaded_at: str


class CacheIndex:
    """Manages the cache index file."""

    def __init__(self, cache_dir: Path) -> None:
        self._path = cache_dir / INDEX_FILE
        self._data: dict[str, CacheEntry] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            for key, entry in raw.items():
                self._data[key] = CacheEntry(**entry)
        except json.JSONDecodeError, TypeError:
            self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        raw = {k: vars(v) for k, v in self._data.items()}
        self._path.write_text(
            json.dumps(raw, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def get(self, key: str) -> CacheEntry | None:
        """Get cache entry by key (e.g. 'rsubtil/controller-icons@v2.0.1')."""
        return self._data.get(key)

    def has(self, key: str) -> bool:
        """Check if key exists in index."""
        return key in self._data

    def put(
        self,
        key: str,
        file: str,
        version: str,
        zip_path: Path,
    ) -> CacheEntry:
        """Add or update cache entry."""
        hash_val = sha256_file(zip_path) if zip_path.exists() else ""
        entry = CacheEntry(
            file=file,
            version=version,
            hash=hash_val,
            downloaded_at=datetime.now(UTC).isoformat(),
        )
        self._data[key] = entry
        self._save()
        return entry

    def remove(self, key: str) -> bool:
        """Remove entry from index."""
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False

    def find_by_slug(self, slug: str) -> list[tuple[str, CacheEntry]]:
        """Find all entries matching a slug (ignoring version)."""
        results = []
        for key, entry in self._data.items():
            if key.startswith(f"{slug}@") or key == slug:
                results.append((key, entry))
        return results

    def list_all(self) -> dict[str, CacheEntry]:
        """Return all entries."""
        return dict(self._data)


def make_cache_key(publisher: str, slug: str, version: str) -> str:
    """Create cache key from publisher, slug and version.

    Example: 'rsubtil/controller-icons@v2.0.1'
    """
    return f"{publisher}/{slug}@{version}"
