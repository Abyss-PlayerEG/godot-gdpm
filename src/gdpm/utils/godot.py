"""Godot project.godot file parser.

Detects Godot engine version from project.godot files.
Supports Godot 3.x and 4.x formats.

Version detection by config_version:
- config_version=5 → Godot 4.x: config/features=PackedStringArray("4.7", "Forward Plus")
- config_version=4 → Godot 3.x: config/version="3.5.2"
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class GodotProject:
    """Parsed Godot project information."""

    name: str = ""
    godot_version: str = ""
    config_version: int = 0
    renderer: str = ""
    features: list[str] | None = None

    @property
    def version_constraint(self) -> str:
        """Return a version constraint string for gdproject.toml."""
        if not self.godot_version:
            return ">=3.0"

        parts = self.godot_version.split(".")
        if len(parts) >= 2:
            major = int(parts[0])
            minor = int(parts[1])
            return f">={major}.{minor}.0"

        return f">={self.godot_version}"


def parse_project_godot(path: Path) -> GodotProject:
    """Parse a project.godot file and extract project information.

    Supports Godot 3.x (config_version=4) and 4.x (config_version=5).
    """
    if not path.exists():
        return GodotProject()

    content = path.read_text(encoding="utf-8")
    project = _parse_content(content)

    if project.config_version > 0 and project.config_version < 4:
        return GodotProject()

    return project


def _parse_content(content: str) -> GodotProject:
    """Parse project.godot content string."""
    project = GodotProject()

    # Parse config_version
    match = re.search(r"config_version=(\d+)", content)
    if match:
        project.config_version = int(match.group(1))

    # Parse project name
    # Godot 4.x/3.x: config/name="..."
    # Godot 2.x/1.x: name="..."
    match = re.search(r'config/name="([^"]+)"', content)
    if not match:
        match = re.search(r'^name="([^"]+)"', content, re.MULTILINE)
    if match:
        project.name = match.group(1)

    # Parse version based on config_version
    if project.config_version >= 5:
        # Godot 4.x: config/features=PackedStringArray("4.7", "Forward Plus")
        match = re.search(r"config/features=PackedStringArray\(([^)]+)\)", content)
        if match:
            features_str = match.group(1)
            features = [
                f.strip().strip('"')
                for f in features_str.split(",")
                if f.strip().strip('"')
            ]
            project.features = features

            # Extract version from features
            for f in features:
                if re.match(r"^\d+\.\d+", f):
                    project.godot_version = f
                    break

            # Extract renderer
            renderers = {
                "Forward Plus": "Forward Plus",
                "Mobile": "Mobile",
                "GL Compatibility": "GL Compatibility",
                "GLES2": "GLES2",
                "GLES3": "GLES3",
            }
            for f in features:
                if f in renderers:
                    project.renderer = renderers[f]
                    break

    elif project.config_version == 4:
        # Godot 3.x: config/version="3.5.2"
        match = re.search(r'config/version="([^"]+)"', content)
        if match:
            project.godot_version = match.group(1)

        # Try to detect renderer
        if "GLES2" in content:
            project.renderer = "GLES2"
        elif "GLES3" in content:
            project.renderer = "GLES3"

    return project


def detect_godot_version(project_dir: Path) -> str:
    """Detect Godot version from project.godot.

    Returns version string like "4.7" or "3.5".
    Returns empty string if not found.
    """
    project_file = project_dir / "project.godot"
    project = parse_project_godot(project_file)
    return project.godot_version


def detect_version_constraint(project_dir: Path) -> str:
    """Detect Godot version constraint for gdproject.toml.

    Returns constraint string like ">=4.2.0".
    Returns ">=4.0" if not found.
    """
    project_file = project_dir / "project.godot"
    project = parse_project_godot(project_file)
    return project.version_constraint


def detect_godot_binary(path: Path) -> Path | None:
    """Detect Godot binary path from a given path.

    For macOS .app bundles, returns the binary inside Contents/MacOS/.
    For Linux/Windows, returns the path directly if it's executable.

    Returns:
        Path to Godot binary, or None if not valid.
    """
    if not path.exists():
        return None

    # macOS .app bundle
    if path.suffix == ".app":
        binary = path / "Contents" / "MacOS" / "Godot"
        if binary.exists():
            return binary
        # Try stem-based name (e.g., Godot_mono.app -> Godot_mono)
        binary = path / "Contents" / "MacOS" / path.stem
        if binary.exists():
            return binary
        return None

    # Linux/Windows executable
    if path.is_file():
        return path

    return None


def get_godot_version(binary: Path) -> str:
    """Get Godot version from binary.

    Runs 'godot --version' and parses the output.

    Returns:
        Version string like '4.7-stable', or empty string if failed.
    """
    try:
        result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return ""

        version_str = result.stdout.strip()
        # "4.7.0.stable.official.h" -> "4.7-stable"
        return _parse_version_string(version_str)
    except Exception:
        return ""


def _parse_version_string(version_str: str) -> str:
    """Parse Godot version string to short format.

    '4.7.0.stable.official.h' -> '4.7-stable'
    '3.6.2.stable.official.h' -> '3.6.2-stable'
    '4.7.0.rc1.official.h' -> '4.7-rc1'
    """
    parts = version_str.split(".")
    if len(parts) < 3:
        return version_str

    major = parts[0]
    minor = parts[1]

    # Find the stability tag (stable, rc, beta, dev)
    stability = ""
    for part in parts[2:]:
        if part in ("stable", "rc", "beta", "dev"):
            stability = part
            break

    if stability:
        return f"{major}.{minor}-{stability}"
    return f"{major}.{minor}"
