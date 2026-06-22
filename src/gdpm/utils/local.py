"""Local plugin management utilities.

Handles scanning, packing, unpacking, and hash-based change detection
for local plugins not published to the Godot Asset Store.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

TAG_FILENAME = "tag.gdpm"
LOCAL_DIR_NAME = "gdpm-local"
LOCAL_TAG_PREFIX = "local+"
HASHES_FILE = ".hashes"


def scan_local_plugins(addons_dir: Path) -> list[Path]:
    """Scan addons/ for local plugins (tagged with local+ prefix)."""
    if not addons_dir.exists():
        return []

    local_plugins: list[Path] = []
    for child in sorted(addons_dir.iterdir()):
        if not child.is_dir():
            continue
        tag_path = child / TAG_FILENAME
        if tag_path.exists():
            tag = tag_path.read_text(encoding="utf-8").strip()
            if tag.startswith(LOCAL_TAG_PREFIX):
                local_plugins.append(child)
    return local_plugins


def scan_untagged_or_local_plugins(addons_dir: Path) -> list[Path]:
    """Scan addons/ for untagged directories or local plugins."""
    if not addons_dir.exists():
        return []

    result: list[Path] = []
    for child in sorted(addons_dir.iterdir()):
        if not child.is_dir():
            continue
        tag_path = child / TAG_FILENAME
        if not tag_path.exists():
            # Untagged
            result.append(child)
        else:
            tag = tag_path.read_text(encoding="utf-8").strip()
            if tag.startswith(LOCAL_TAG_PREFIX):
                # Local plugin
                result.append(child)
    return result


def tag_plugin(addons_dir: Path, plugin_dir_name: str) -> None:
    """Write local tag to a plugin directory."""
    tag_path = addons_dir / plugin_dir_name / TAG_FILENAME
    tag_path.write_text(
        f"{LOCAL_TAG_PREFIX}{plugin_dir_name}",
        encoding="utf-8",
    )


def compute_dir_hash(dir_path: Path) -> str:
    """Compute SHA256 hash of a directory's contents."""
    h = hashlib.sha256()
    for file in sorted(dir_path.rglob("*")):
        if file.is_file() and file.name != TAG_FILENAME:
            rel = str(file.relative_to(dir_path))
            h.update(rel.encode())
            h.update(file.read_bytes())
    return h.hexdigest()


def load_hashes(project_root: Path) -> dict[str, str]:
    """Load hash records from gdpm-local/.hashes."""
    hashes_path = project_root / LOCAL_DIR_NAME / HASHES_FILE
    if not hashes_path.exists():
        return {}

    try:
        data: dict[str, str] = json.loads(hashes_path.read_text(encoding="utf-8"))
        return data
    except json.JSONDecodeError, OSError:
        return {}


def save_hashes(project_root: Path, hashes: dict[str, str]) -> None:
    """Save hash records to gdpm-local/.hashes."""
    local_dir = project_root / LOCAL_DIR_NAME
    local_dir.mkdir(parents=True, exist_ok=True)
    hashes_path = local_dir / HASHES_FILE
    hashes_path.write_text(
        json.dumps(hashes, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def find_matching_hash(
    hashes: dict[str, str],
    content_hash: str,
) -> str | None:
    """Find a plugin name that matches the given hash."""
    for name, h in hashes.items():
        if h == content_hash:
            return name
    return None


def pack_plugin(addons_dir: Path, plugin_dir_name: str, dest_dir: Path) -> Path:
    """Pack a plugin directory into a zip file."""
    source = addons_dir / plugin_dir_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / f"{plugin_dir_name}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in source.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(source)
                zf.write(file, arcname)

    return zip_path


def unpack_plugin(zip_path: Path, addons_dir: Path) -> str:
    """Unpack a local plugin zip to addons/ directory."""
    dir_name = zip_path.stem
    dest = addons_dir / dir_name
    dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)

    tag_plugin(addons_dir, dir_name)
    return dir_name


def sync_local_plugins(project_root: Path, addons_dir: Path) -> list[str]:
    """Sync local plugins from gdpm-local/ to addons/.

    Returns list of synced plugin names.
    """
    local_dir = project_root / LOCAL_DIR_NAME
    if not local_dir.exists():
        return []

    synced: list[str] = []
    for zip_file in sorted(local_dir.glob("*.zip")):
        name = unpack_plugin(zip_file, addons_dir)
        synced.append(name)

    return synced


def get_local_plugin_names(project_root: Path) -> list[str]:
    """Get list of local plugin names from gdpm-local/."""
    local_dir = project_root / LOCAL_DIR_NAME
    if not local_dir.exists():
        return []

    return [f.stem for f in sorted(local_dir.glob("*.zip"))]
