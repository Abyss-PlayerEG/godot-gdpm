"""Godot project.godot file parser.

Detects Godot engine version from project.godot files.
Supports Godot 1.x through 4.x formats.

Version detection by config_version:
- config_version=5 → Godot 4.x: config/features=PackedStringArray("4.7", "Forward Plus")
- config_version=4 → Godot 3.x: config/version="3.5.2"
- config_version=2 → Godot 2.x: version="2.1.6"
- config_version=1 → Godot 1.x: version="1.1.0"
"""

from __future__ import annotations

import re
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
            return ">=4.0"

        parts = self.godot_version.split(".")
        if len(parts) >= 2:
            major = int(parts[0])
            minor = int(parts[1])
            return f">={major}.{minor}.0"

        return f">={self.godot_version}"


def parse_project_godot(path: Path) -> GodotProject:
    """Parse a project.godot file and extract project information."""
    if not path.exists():
        return GodotProject()

    content = path.read_text(encoding="utf-8")
    return _parse_content(content)


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

    elif project.config_version <= 2:
        # Godot 2.x/1.x: version="2.1.6"
        match = re.search(r'^version="([^"]+)"', content, re.MULTILINE)
        if match:
            project.godot_version = match.group(1)

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
