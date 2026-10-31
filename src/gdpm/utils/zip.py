"""
ZIP 解压工具, 分析压缩包结构并按插件布局解压 addon 与资产.

ZIP extraction utilities. Analyze zip structure and extract addons and
assets according to plugin layout.

----

Note:
    - ZipAnalysis: 压缩包结构分析结果 / Zip structure analysis result.
    - analyze_zip: 分析压缩包结构 / Analyze zip structure.
    - extract_addon_from_zip: 按 addon 布局解压 / Extract by addon
        layout.
    - extract_zip / extract_full_zip: 完整解压 / Full extraction.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ZipAnalysis:
    """
    压缩包结构分析结果.

    Zip structure analysis result.

    ----

    Attributes:
        has_addons: 是否包含 addon / Whether the archive contains addons.
        has_assets: 是否包含资产目录 / Whether it contains asset
            directories.
        addon_dirs: addon 目录名列表 / List of addon directory names.
        asset_dirs: 资产目录名列表 / List of asset directory names.
    """

    has_addons: bool = False
    has_assets: bool = False
    addon_dirs: list[str] | None = None
    asset_dirs: list[str] | None = None


def analyze_zip(zip_path: Path) -> ZipAnalysis:
    """
    分析压缩包的目录结构, 识别 addons/ 布局, plugin.cfg 插件目录与资产目录.

    Analyze the directory structure of a zip archive. Detects addons/
    layout, plugin.cfg plugin dirs and asset dirs.

    ----

    Args:
        zip_path: 压缩包路径 / Path to the zip archive.

    Returns:
        压缩包结构分析结果 / Zip structure analysis result.
    """
    result = ZipAnalysis()
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()

        # 收集顶层目录 / Collect top-level directories
        root_dirs: set[str] = set()
        for member in members:
            parts = member.split("/")
            if len(parts) > 1 and parts[0]:
                root_dirs.add(parts[0])

        # 定位 addons/ 前缀并收集 addon 目录 /
        # Locate the addons/ prefix and collect addon directories
        addon_dirs: set[str] = set()
        for member in members:
            if member.startswith("addons/") or "/addons/" in member:
                prefix = "addons/"
                if "/addons/" in member:
                    idx = member.index("/addons/")
                    prefix = member[: idx + len("/addons/")]

                rel = member[len(prefix) :]
                if rel:
                    parts = rel.split("/")
                    if len(parts) > 1 and parts[0]:
                        addon_dirs.add(parts[0])

        if addon_dirs:
            result.has_addons = True
            result.addon_dirs = sorted(addon_dirs)

        # 含 plugin.cfg 的顶层目录视为插件 /
        # Treat top-level dirs containing plugin.cfg as plugins
        for root_dir in root_dirs:
            plugin_cfg = f"{root_dir}/plugin.cfg"
            if plugin_cfg in members:
                if not result.has_addons:
                    result.has_addons = True
                    result.addon_dirs = []
                if result.addon_dirs is not None:
                    result.addon_dirs.append(root_dir)

        # 仅有一个顶层目录时视其为插件 / A single top-level dir is treated as a plugin
        if not result.has_addons and len(root_dirs) == 1:
            single_dir = root_dirs.pop()
            result.has_addons = True
            result.addon_dirs = [single_dir]

        # 资产目录特征名 / Asset directory indicators
        asset_indicators = {
            "assets",
            "sprites",
            "models",
            "animations",
            "sounds",
            "audio",
            "textures",
            "fonts",
        }
        asset_dirs = [d for d in root_dirs if d.lower() in asset_indicators]
        if asset_dirs:
            result.has_assets = True
            result.asset_dirs = sorted(asset_dirs)

    return result


def extract_zip(zip_path: Path, dest: Path) -> None:
    """
    将压缩包完整解压到目标目录.

    Extract the full zip archive into the destination directory.

    ----

    Args:
        zip_path: 压缩包路径 / Path to the zip archive.
        dest: 解压目标目录 / Destination directory.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)


def extract_addon_from_zip(zip_path: Path, dest: Path, addon_name: str) -> list[str]:
    """
    按 addon 布局从压缩包解压插件, 依次尝试 addons/ 前缀, plugin.cfg
    目录与单一顶层目录.

    Extract an addon from a zip archive by addon layout. Tries the
    addons/ prefix, then plugin.cfg dirs, then a single top dir.

    ----

    Args:
        zip_path: 压缩包路径 / Path to the zip archive.
        dest: 解压目标目录 / Destination directory.
        addon_name: 插件名称 / Addon name.

    Returns:
        解压得到的 addon 目录名列表, 失败时返回空列表 /
            List of extracted addon directory names, empty on failure.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        if not members:
            return []

        addon_prefix = None
        preserve_dir = False

        # 第一优先级: 根部或嵌套的 addons/ 前缀 /
        # First priority: root or nested addons/ prefix
        for member in members:
            if member.startswith("addons/"):
                addon_prefix = "addons/"
                break
            if "/addons/" in member:
                idx = member.index("/addons/")
                addon_prefix = member[: idx + len("/addons/")]
                break

        # 第二优先级: 含 plugin.cfg 的顶层目录 /
        # Second priority: top-level dir containing plugin.cfg
        if addon_prefix is None:
            root_dirs: set[str] = set()
            for member in members:
                parts = member.split("/")
                if len(parts) > 1 and parts[0]:
                    root_dirs.add(parts[0])

            for root_dir in root_dirs:
                if f"{root_dir}/plugin.cfg" in members:
                    addon_prefix = f"{root_dir}/"
                    preserve_dir = True
                    break

        # 第三优先级: 单一顶层目录 / Third priority: a single top-level dir
        if addon_prefix is None:
            root_dirs = set()
            for member in members:
                parts = member.split("/")
                if len(parts) > 1 and parts[0]:
                    root_dirs.add(parts[0])

            if len(root_dirs) == 1:
                addon_prefix = f"{root_dirs.pop()}/"
                preserve_dir = True

        if addon_prefix is None:
            return []

        addon_dirs: set[str] = set()

        for member in members:
            if not member.startswith(addon_prefix):
                continue

            rel = member[len(addon_prefix) :]
            if not rel:
                continue

            parts = rel.split("/")
            if len(parts) > 1 and parts[0]:
                addon_dirs.add(parts[0])

            if preserve_dir:
                dir_name = addon_prefix.rstrip("/")
                target = dest / dir_name / rel
            else:
                target = dest / rel

            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    dst.write(src.read())

        if preserve_dir:
            dir_name = addon_prefix.rstrip("/")
            return [dir_name]
        return sorted(addon_dirs)


def extract_full_zip(zip_path: Path, dest: Path) -> None:
    """
    将压缩包完整解压到目标目录.

    Extract the full zip archive into the destination directory.

    ----

    Args:
        zip_path: 压缩包路径 / Path to the zip archive.
        dest: 解压目标目录 / Destination directory.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
