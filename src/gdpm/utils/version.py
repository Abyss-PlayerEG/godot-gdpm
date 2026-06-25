"""Version normalization and parsing utilities.

Provides lenient version parsing compatible with non-standard formats
commonly found in Godot Asset Store (e.g., "4.6.2-stable", "V1.1").
"""

from __future__ import annotations

import re

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


def normalize_version(version: str) -> str:
    """Normalize a version string to PEP 440 compatible format.

    Handles common non-standard formats:
    - "v1.0.0" → "1.0.0"
    - "V2.0" → "2.0"
    - "1.0.0-stable" → "1.0.0.stable"
    - "1.0.0-beta1" → "1.0.0.beta1"
    - "1.0.0-rc2" → "1.0.0.rc2"
    """
    if not version:
        return "0.0.0"

    v = version.strip()

    # Remove v/V prefix
    v = re.sub(r"^[vV]+", "", v)

    # Handle -stable, -beta, -alpha, -rc suffixes
    # -stable → .stable
    # -beta1 → .beta1
    # -rc2 → .rc2
    v = re.sub(r"-(stable|alpha|beta|rc)(\d*)$", r".\1\2", v, flags=re.IGNORECASE)

    # Replace remaining hyphens with dots
    v = v.replace("-", ".")

    # Remove any non-alphanumeric characters except dots
    v = re.sub(r"[^a-zA-Z0-9.]", "", v)

    # Ensure it starts with a digit
    if not v or not v[0].isdigit():
        v = "0.0.0"

    return v


def normalize_constraint(constraint: str) -> str:
    """Normalize a version constraint string.

    Handles:
    - ">=v1.0.0" → ">=1.0.0"
    - "^1.0.0" → ">=1.0.0,<2.0.0"
    - "~1.0.0" → ">=1.0.0,<1.1.0"
    - "v1.0.0" → "==1.0.0"
    """
    c = constraint.strip()

    # Handle caret constraint
    if c.startswith("^"):
        base = normalize_version(c[1:])
        parts = base.split(".")
        major = int(parts[0])
        return f">={base},<{major + 1}.0.0"

    # Handle tilde constraint
    if c.startswith("~"):
        base = normalize_version(c[1:])
        parts = base.split(".")
        major, minor = int(parts[0]), int(parts[1])
        return f">={base},<{major}.{minor + 1}.0"

    # Handle wildcard
    if c == "*":
        return ">=0.0.0"

    # Normalize version in constraint operators
    # >=v1.0.0 → >=1.0.0
    # ==V2.0 → ==2.0
    c = re.sub(
        r"([><=!~]+)\s*[vV]?(\d[\w.]*)",
        lambda m: m.group(1) + normalize_version(m.group(2)),
        c,
    )

    return c


def parse_version(version: str) -> Version:
    """Parse a version string, normalizing it first."""
    normalized = normalize_version(version)
    return Version(normalized)


def parse_specifier_set(constraint: str) -> SpecifierSet:
    """Parse a version constraint, normalizing it first."""
    normalized = normalize_constraint(constraint)
    return SpecifierSet(normalized)


def version_matches(version: str, constraint: str) -> bool:
    """Check if a version matches a constraint."""
    try:
        # Wildcard always matches
        if constraint.strip() == "*":
            return True

        ver = parse_version(version)
        spec = parse_specifier_set(constraint)
        return ver in spec
    except (InvalidVersion, InvalidSpecifier):
        # Fallback: string comparison
        return normalize_version(version) == normalize_version(constraint)


def is_compatible(
    project_godot: str,
    min_godot: str,
    max_godot: str,
) -> tuple[bool, str]:
    """Check if a plugin is compatible with the project's Godot version.

    Returns (compatible, message).
    """
    if not project_godot or project_godot == "*":
        return True, ""

    # Filter out None/empty values
    min_godot = min_godot if min_godot and min_godot != "None" else ""
    max_godot = max_godot if max_godot and max_godot != "None" else ""

    min_v = normalize_version(min_godot) if min_godot else ""
    max_v = normalize_version(max_godot) if max_godot else ""

    if not min_v and not max_v:
        return True, ""

    try:
        # Extract the base version from the project constraint
        # ">=4.2.0" → "4.2.0"
        # ">=4.2.0,<5.0.0" → "4.2.0"
        base = re.sub(r"[><=!~^*\s]", "", project_godot)
        base = base.split(",")[0].strip()
        project_ver = parse_version(base)

        if max_v:
            max_ver = parse_version(max_v)
            if project_ver > max_ver:
                return False, (
                    f"Plugin supports Godot <={max_godot}, "
                    f"but project uses {project_godot}"
                )

        if min_v:
            min_ver = parse_version(min_v)
            if project_ver < min_ver:
                return False, (
                    f"Plugin requires Godot >={min_godot}, "
                    f"but project uses {project_godot}"
                )

    except (InvalidVersion, ValueError):
        pass

    return True, ""
