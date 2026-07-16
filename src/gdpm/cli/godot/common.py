"""Shared utilities for gdpm godot commands."""

from __future__ import annotations

from pathlib import Path

import httpx

from gdpm.constants import GITHUB_API_URL, GODOT_RELEASES_URL, get_github_headers
from gdpm.utils.install import get_godot_platform


def get_engines_dir() -> Path:
    """Get the global engines directory."""
    engines_dir = Path.home() / ".gdpm" / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    return engines_dir


def normalize_version(version: str) -> str:
    """Normalize version string to tag format.

    '4.7' -> '4.7-stable'
    '4.7-stable' -> '4.7-stable'
    '3.6.2' -> '3.6.2-stable'
    '4.7-stable-csharp' -> '4.7-stable'
    """
    version = version.replace("-csharp", "").replace("-mono", "")

    if "-stable" in version or "-rc" in version or "-beta" in version:
        return version
    return f"{version}-stable"


def build_download_url(tag: str, csharp: bool = False) -> str:
    """Get Godot download URL from GitHub API."""
    mono = "_mono" if csharp else ""
    system = get_godot_platform()

    if "macos" in system:
        keywords: tuple[str, ...] = ("osx", "macos")
    elif "linux" in system:
        keywords = ("linux",)
    else:
        keywords = ("win",)

    try:
        resp = httpx.get(
            f"{GODOT_RELEASES_URL}/tags/{tag}",
            headers=get_github_headers(),
            timeout=10,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()

        for asset in data.get("assets", []):
            name = asset["name"]
            if mono and "_mono" not in name:
                continue
            if not mono and "_mono" in name:
                continue
            if name.endswith(".zip") and any(k in name for k in keywords):
                return str(asset["browser_download_url"])
    except Exception:
        pass

    return ""


def get_asset_hash(tag: str, filename: str) -> str:
    """Get SHA256 hash for a release asset from GitHub API."""
    try:
        resp = httpx.get(
            f"{GITHUB_API_URL}contributors",
            headers=get_github_headers(),
            timeout=5,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()

        for asset in data.get("assets", []):
            if asset.get("name") == filename:
                digest = asset.get("digest", "")
                if digest.startswith("sha256:"):
                    return str(digest[7:])
        return ""
    except Exception:
        return ""


def find_engine(name: str, version: str) -> str | None:
    """Find Godot binary path by name and version.

    Returns:
        Path string to Godot binary, or None if not found.
    """
    from gdpm.config.local_engines import load_local_engines

    engines_dir = get_engines_dir()

    local_engines = load_local_engines()
    if name in local_engines:
        engine = local_engines[name]
        if not version or engine.version == version:
            return engine.path

    if name == "gdpm-godot":
        tag = normalize_version(version) if version else ""
        if tag:
            ver_dir = engines_dir / tag
            if ver_dir.exists():
                for app in ver_dir.glob("*.app"):
                    binary = app / "Contents" / "MacOS" / "Godot"
                    if binary.exists():
                        return str(binary)
                for f in ver_dir.iterdir():
                    if f.is_file() and not f.suffix:
                        return str(f)

    return None
