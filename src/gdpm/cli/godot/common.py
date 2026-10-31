"""Shared utilities for gdpm godot commands."""

from __future__ import annotations

import os
import platform
import subprocess
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


def ensure_executable(path: Path) -> None:
    """Ensure a file has execute permission (no-op on Windows)."""
    if platform.system() == "Windows":
        return
    try:
        if not os.access(path, os.X_OK):
            path.chmod(path.stat().st_mode | 0o111)
    except OSError:
        pass


def find_engine_binary(directory: Path) -> str | None:
    """Find launchable Godot binary inside an engine directory (cross-platform).

    Handles:
    - macOS: .app bundle -> Contents/MacOS/Godot, fallback to extensionless binary
    - Windows: .exe (prefers non-console), including mono subdirectory layout
    - Linux: Godot* executable (names end with .x86_64/.arm64), restores exec bit
    """
    system = platform.system()

    search_dirs = [directory]
    try:
        search_dirs.extend(
            child
            for child in directory.iterdir()
            if child.is_dir() and child.name != "GodotSharp"
        )
    except OSError:
        return None

    if system == "Darwin":
        for d in search_dirs:
            for app in sorted(d.glob("*.app")):
                binary = app / "Contents" / "MacOS" / "Godot"
                if binary.exists():
                    return str(binary)

    if system == "Windows":
        exes: list[Path] = []
        for d in search_dirs:
            try:
                exes.extend(
                    f for f in d.iterdir() if f.is_file() and f.suffix.lower() == ".exe"
                )
            except OSError:
                continue
        for f in exes:
            if "console" not in f.name.lower():
                return str(f)
        if exes:
            return str(exes[0])
        return None

    for d in search_dirs:
        try:
            for f in sorted(d.iterdir()):
                if (
                    f.is_file()
                    and f.name.startswith("Godot")
                    and not f.name.endswith(".zip")
                ):
                    ensure_executable(f)
                    return str(f)
        except OSError:
            continue

    if system == "Darwin":
        for d in search_dirs:
            try:
                for f in sorted(d.iterdir()):
                    if f.is_file() and not f.suffix:
                        ensure_executable(f)
                        return str(f)
            except OSError:
                continue

    return None


def prepare_engine_dir(directory: Path) -> None:
    """Fix permissions after extracting a Godot release archive (platform-aware)."""
    if platform.system() == "Darwin":
        for app in directory.glob("*.app"):
            subprocess.run(
                ["xattr", "-cr", str(app)],
                check=False,
                capture_output=True,
            )
            macos_dir = app / "Contents" / "MacOS"
            if macos_dir.exists():
                for binary in macos_dir.iterdir():
                    ensure_executable(binary)

    if platform.system() != "Windows":
        for f in directory.rglob("*"):
            if (
                f.is_file()
                and f.name.startswith("Godot")
                and "GodotSharp" not in f.parts
            ):
                ensure_executable(f)


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
            for candidate in (engines_dir / tag, engines_dir / f"{tag}-csharp"):
                if candidate.exists():
                    binary = find_engine_binary(candidate)
                    if binary:
                        return binary

    return None


def resolve_engine_path(name: str, version: str) -> str:
    """Resolve Godot binary path by engine name and version.

    Less strict than find_engine: local engines are matched by name only.
    """
    from gdpm.config.local_engines import get_local_engine

    if name == "gdpm-godot":
        engines_dir = get_engines_dir()
        tag = normalize_version(version) if version else ""
        if tag:
            for candidate in (engines_dir / tag, engines_dir / f"{tag}-csharp"):
                if candidate.exists():
                    binary = find_engine_binary(candidate)
                    if binary:
                        return binary
        return ""

    engine = get_local_engine(name)
    return engine.path if engine else ""
