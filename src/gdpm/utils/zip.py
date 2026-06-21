"""ZIP extraction utilities."""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def extract_zip(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)


def extract_addon_from_zip(zip_path: Path, dest: Path, addon_name: str) -> list[str]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        if not members:
            return []

        addon_prefix = None

        for member in members:
            if member.startswith("addons/"):
                addon_prefix = "addons/"
                break
            if "/addons/" in member:
                idx = member.index("/addons/")
                addon_prefix = member[: idx + len("/addons/")]
                break

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

            target = dest / rel
            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    dst.write(src.read())

        return sorted(addon_dirs)
