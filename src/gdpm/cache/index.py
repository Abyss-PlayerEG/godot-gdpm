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
    hash: str
    downloaded_at: str


class CacheIndex:
    """Manages cache index files (split by first letter)."""

    def __init__(self, downloads_dir: Path) -> None:
        self._downloads = downloads_dir
        self._cache: dict[str, dict[str, CacheEntry]] = {}

    def _get_index_path(self, letter: str) -> Path:
        return self._downloads / letter / INDEX_FILE

    def _load_letter(self, letter: str) -> dict[str, CacheEntry]:
        if letter in self._cache:
            return self._cache[letter]

        path = self._get_index_path(letter)
        data: dict[str, CacheEntry] = {}

        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                for key, entry in raw.items():
                    data[key] = CacheEntry(**entry)
            except (json.JSONDecodeError, TypeError):
                data = {}

        self._cache[letter] = data
        return data

    def _save_letter(self, letter: str) -> None:
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
        publisher = key.split("/")[0] if "/" in key else key
        return publisher[0].lower() if publisher else "x"

    def get(self, key: str) -> CacheEntry | None:
        letter = self._letter_for_key(key)
        data = self._load_letter(letter)
        return data.get(key)

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def put(
        self,
        key: str,
        file: str,
        zip_path: Path,
    ) -> CacheEntry:
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
        letter = self._letter_for_key(key)
        data = self._load_letter(letter)
        if key in data:
            del data[key]
            self._save_letter(letter)
            return True
        return False

    def find_by_slug(self, slug: str) -> list[tuple[str, CacheEntry]]:
        results = []
        for letter_dir in self._downloads.iterdir():
            if not letter_dir.is_dir():
                continue
            data = self._load_letter(letter_dir.name)
            for key, entry in data.items():
                if key.startswith(f"{slug}@") or key == slug:
                    results.append((key, entry))
        return results

    def list_all(self) -> dict[str, CacheEntry]:
        result: dict[str, CacheEntry] = {}
        for letter_dir in self._downloads.iterdir():
            if not letter_dir.is_dir():
                continue
            data = self._load_letter(letter_dir.name)
            result.update(data)
        return result


def make_cache_key(publisher: str, slug: str, version: str) -> str:
    """Create cache key from publisher, slug and version.

    Example: 'rsubtil/controller-icons@v2.0.1'
    """
    return f"{publisher}/{slug}@{version}"
