"""
本地插件管理工具, 处理未发布到 Godot Asset Store 的本地插件的扫描,
打包, 解包与基于哈希的变更检测.

Local plugin management utilities. Handle scanning, packing, unpacking,
and hash-based change detection for local plugins not published to the
Godot Asset Store.

----

Note:
    - scan_*: 扫描本地插件 / Scan local plugins.
    - pack_plugin / unpack_plugin: 打包与解包插件 / Pack and unpack
        plugins.
    - compute_dir_hash / load_hashes / save_hashes: 哈希变更检测 /
        Hash-based change detection.
    - sync_local_plugins: 同步本地插件到 addons/ / Sync local plugins to
        addons/.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# 标记文件与本地插件目录相关常量 /
# Constants for tag files and the local plugin directory
TAG_FILENAME = "tag.gdpm"
LOCAL_DIR_NAME = "gdpm-local"
LOCAL_TAG_PREFIX = "local+"
HASHES_FILE = ".hashes"


def scan_local_plugins(addons_dir: Path) -> list[Path]:
    """
    扫描 addons/ 下带 local+ 标记的本地插件.

    Scan addons/ for local plugins (tagged with local+ prefix).

    ----

    Args:
        addons_dir: addons 目录路径 / Path to the addons directory.

    Returns:
        本地插件目录列表 / List of local plugin directories.
    """
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
    """
    扫描 addons/ 下未打标记或本地插件的目录.

    Scan addons/ for untagged directories or local plugins.

    ----

    Args:
        addons_dir: addons 目录路径 / Path to the addons directory.

    Returns:
        未打标记或本地插件的目录列表 /
            List of untagged or local plugin directories.
    """
    if not addons_dir.exists():
        return []

    result: list[Path] = []
    for child in sorted(addons_dir.iterdir()):
        if not child.is_dir():
            continue
        tag_path = child / TAG_FILENAME
        if not tag_path.exists():
            # 未打标记 / Untagged
            result.append(child)
        else:
            tag = tag_path.read_text(encoding="utf-8").strip()
            if tag.startswith(LOCAL_TAG_PREFIX):
                # 本地插件 / Local plugin
                result.append(child)
    return result


def tag_plugin(addons_dir: Path, plugin_dir_name: str) -> None:
    """
    向插件目录写入本地标记.

    Write local tag to a plugin directory.

    ----

    Args:
        addons_dir: addons 目录路径 / Path to the addons directory.
        plugin_dir_name: 插件目录名 / Plugin directory name.
    """
    tag_path = addons_dir / plugin_dir_name / TAG_FILENAME
    tag_path.write_text(
        f"{LOCAL_TAG_PREFIX}{plugin_dir_name}",
        encoding="utf-8",
    )


def compute_dir_hash(dir_path: Path) -> str:
    """
    计算目录内容的 SHA256 哈希, 标记文件不参与哈希计算.

    Compute SHA256 hash of a directory's contents. The tag file is
    excluded from the hash.

    ----

    Args:
        dir_path: 插件目录路径 / Path to the plugin directory.

    Returns:
        十六进制哈希字符串 / Hex digest string.
    """
    h = hashlib.sha256()
    for file in sorted(dir_path.rglob("*")):
        if file.is_file() and file.name != TAG_FILENAME:
            rel = str(file.relative_to(dir_path))
            h.update(rel.encode())
            h.update(file.read_bytes())
    return h.hexdigest()


def load_hashes(project_root: Path) -> dict[str, str]:
    """
    从 gdpm-local/.hashes 加载哈希记录.

    Load hash records from gdpm-local/.hashes.

    ----

    Args:
        project_root: 项目根目录 / Project root directory.

    Returns:
        插件名到哈希的映射, 文件缺失或损坏时返回空字典 /
            Mapping of plugin name to hash, empty dict when the file is
            missing or invalid.
    """
    hashes_path = project_root / LOCAL_DIR_NAME / HASHES_FILE
    if not hashes_path.exists():
        return {}

    try:
        data: dict[str, str] = json.loads(hashes_path.read_text(encoding="utf-8"))
        return data
    except json.JSONDecodeError, OSError:
        return {}


def save_hashes(project_root: Path, hashes: dict[str, str]) -> None:
    """
    将哈希记录保存到 gdpm-local/.hashes.

    Save hash records to gdpm-local/.hashes.

    ----

    Args:
        project_root: 项目根目录 / Project root directory.
        hashes: 插件名到哈希的映射 / Mapping of plugin name to hash.
    """
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
    """
    查找与给定哈希匹配的插件名.

    Find a plugin name that matches the given hash.

    ----

    Args:
        hashes: 插件名到哈希的映射 / Mapping of plugin name to hash.
        content_hash: 待匹配的哈希 / Hash to match.

    Returns:
        匹配的插件名, 无匹配时返回 None /
            Matching plugin name, or None if no match.
    """
    for name, h in hashes.items():
        if h == content_hash:
            return name
    return None


def pack_plugin(addons_dir: Path, plugin_dir_name: str, dest_dir: Path) -> Path:
    """
    将插件目录打包为 zip 文件.

    Pack a plugin directory into a zip file.

    ----

    Args:
        addons_dir: addons 目录路径 / Path to the addons directory.
        plugin_dir_name: 插件目录名 / Plugin directory name.
        dest_dir: 输出目录 / Destination directory.

    Returns:
        生成的 zip 文件路径 / Path to the created zip file.
    """
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
    """
    将本地插件 zip 解包到 addons/ 目录, 解包后自动写入本地标记.

    Unpack a local plugin zip to addons/ directory. Writes the local tag
    automatically after unpacking.

    ----

    Args:
        zip_path: 插件 zip 文件路径 / Path to the plugin zip file.
        addons_dir: addons 目录路径 / Path to the addons directory.

    Returns:
        解包得到的插件目录名 / Name of the unpacked plugin directory.
    """
    dir_name = zip_path.stem
    dest = addons_dir / dir_name
    dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)

    tag_plugin(addons_dir, dir_name)
    return dir_name


def sync_local_plugins(project_root: Path, addons_dir: Path) -> list[str]:
    """
    将本地插件从 gdpm-local/ 同步到 addons/.

    Sync local plugins from gdpm-local/ to addons/.

    ----

    Args:
        project_root: 项目根目录 / Project root directory.
        addons_dir: addons 目录路径 / Path to the addons directory.

    Returns:
        已同步的插件名列表 / List of synced plugin names.
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
    """
    获取 gdpm-local/ 下的本地插件名列表.

    Get list of local plugin names from gdpm-local/.

    ----

    Args:
        project_root: 项目根目录 / Project root directory.

    Returns:
        本地插件名列表 / List of local plugin names.
    """
    local_dir = project_root / LOCAL_DIR_NAME
    if not local_dir.exists():
        return []

    return [f.stem for f in sorted(local_dir.glob("*.zip"))]
