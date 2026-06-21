"""ZIP extraction utilities."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ZipAnalysis:
    has_addons: bool = False
    has_assets: bool = False
    addon_dirs: list[str] | None = None
    asset_dirs: list[str] | None = None


def analyze_zip(zip_path: Path) -> ZipAnalysis:
    result = ZipAnalysis()
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()

        root_dirs: set[str] = set()
        for member in members:
            parts = member.split("/")
            if len(parts) > 1 and parts[0]:
                root_dirs.add(parts[0])

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

        for root_dir in root_dirs:
            plugin_cfg = f"{root_dir}/plugin.cfg"
            if plugin_cfg in members:
                if not result.has_addons:
                    result.has_addons = True
                    result.addon_dirs = []
                if result.addon_dirs is not None:
                    result.addon_dirs.append(root_dir)

        if not result.has_addons and len(root_dirs) == 1:
            single_dir = root_dirs.pop()
            result.has_addons = True
            result.addon_dirs = [single_dir]

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
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)


def extract_addon_from_zip(zip_path: Path, dest: Path, addon_name: str) -> list[str]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        if not members:
            return []

        addon_prefix = None
        preserve_dir = False

        for member in members:
            if member.startswith("addons/"):
                addon_prefix = "addons/"
                break
            if "/addons/" in member:
                idx = member.index("/addons/")
                addon_prefix = member[: idx + len("/addons/")]
                break

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
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
