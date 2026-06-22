#!/usr/bin/env python3
"""Version management script for gdpm.

Usage:
    python scripts/version.py                    # Interactive mode
    python scripts/version.py 0.0.3              # Update version only
    python scripts/version.py 0.0.3 beta         # Update version + tag
    python scripts/version.py 0.0.3 ""           # Update version, clear tag (stable)

Supported tags (PyPI compatible):
    ""      → 0.0.3        (stable)
    "dev"   → 0.0.3.dev1   (development)
    "alpha" → 0.0.3a1      (alpha)
    "beta"  → 0.0.3b1      (beta)
    "rc"    → 0.0.3rc1     (release candidate)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent

PYPROJECT_FILE = PROJECT_DIR / "pyproject.toml"
INIT_FILE = PROJECT_DIR / "src" / "gdpm" / "__init__.py"

VALID_TAGS = ["", "dev", "alpha", "beta", "rc"]

# PyPI version format mapping
TAG_FORMATS = {
    "": "{version}",
    "dev": "{version}.dev1",
    "alpha": "{version}a1",
    "beta": "{version}b1",
    "rc": "{version}rc1",
}


def read_current() -> tuple[str, str]:
    """Read current version and tag from __init__.py."""
    content = INIT_FILE.read_text(encoding="utf-8")

    version_match = re.search(r'__version__\s*=\s*"([^"]*)"', content)
    tag_match = re.search(r'__tag__\s*=\s*"([^"]*)"', content)

    pypi_version = version_match.group(1) if version_match else "0.0.0"
    tag = tag_match.group(1) if tag_match else ""

    # Extract base version from PyPI format
    # "0.0.2b1" → "0.0.2"
    # "0.0.2.dev1" → "0.0.2"
    # "0.0.2" → "0.0.2"
    base_version = re.sub(r"(\.dev\d+|[a-z]\d+|rc\d+)$", "", pypi_version)

    return base_version, tag


def get_pypi_version(version: str, tag: str) -> str:
    """Get PyPI-compatible version string."""
    if not tag:
        return version
    return TAG_FORMATS.get(tag, version).format(version=version)


def get_display_version(version: str, tag: str) -> str:
    """Get display version string."""
    pypi = get_pypi_version(version, tag)
    if tag:
        return f"{pypi} ({tag})"
    return f"{pypi} (stable)"


def update_files(version: str, tag: str) -> None:
    """Update pyproject.toml and __init__.py."""
    pypi_version = get_pypi_version(version, tag)

    # Update pyproject.toml
    content = PYPROJECT_FILE.read_text(encoding="utf-8")
    content = re.sub(
        r'^version\s*=\s*"[^"]*"',
        f'version = "{pypi_version}"',
        content,
        flags=re.MULTILINE,
    )
    PYPROJECT_FILE.write_text(content, encoding="utf-8")

    # Update __init__.py
    content = INIT_FILE.read_text(encoding="utf-8")
    content = re.sub(
        r'__version__\s*=\s*"[^"]*"',
        f'__version__ = "{pypi_version}"',
        content,
    )
    content = re.sub(
        r'__tag__\s*=\s*"[^"]*"',
        f'__tag__ = "{tag}"',
        content,
    )
    INIT_FILE.write_text(content, encoding="utf-8")


def validate_version(version: str) -> bool:
    """Validate version format (x.y.z)."""
    return bool(re.match(r"^\d+\.\d+\.\d+$", version))


def main() -> None:
    current_version, current_tag = read_current()

    # Interactive mode if no arguments
    if len(sys.argv) < 2:
        print(f"Current version: {get_display_version(current_version, current_tag)}")
        print()

        new_version = input("New version (empty to skip): ").strip()
        if not new_version:
            print("No changes.")
            return

        print(f"Tags: {', '.join(VALID_TAGS)} (empty = stable)")
        new_tag = input("Tag (empty = stable): ").strip()

        if new_tag and new_tag not in VALID_TAGS:
            print(f"Error: Invalid tag '{new_tag}'")
            sys.exit(1)

        # Empty input means stable (clear tag)
        update_files(new_version, new_tag)
        _print_result(current_version, current_tag, new_version, new_tag)
        return

    # Command-line mode
    new_version = sys.argv[1]
    new_tag = sys.argv[2] if len(sys.argv) > 2 else current_tag

    if not validate_version(new_version):
        print(f"Error: Invalid version format '{new_version}'. Use x.y.z")
        sys.exit(1)

    if new_tag not in VALID_TAGS:
        print(f"Error: Invalid tag '{new_tag}'. Use: {', '.join(VALID_TAGS)}")
        sys.exit(1)

    update_files(new_version, new_tag)
    _print_result(current_version, current_tag, new_version, new_tag)


def _print_result(old_ver: str, old_tag: str, new_ver: str, new_tag: str) -> None:
    """Print update result."""
    old_display = get_display_version(old_ver, old_tag)
    new_display = get_display_version(new_ver, new_tag)

    print(f"\nUpdated: {old_display} → {new_display}")
    print()
    print("pyproject.toml:")
    for line in PYPROJECT_FILE.read_text().splitlines():
        if line.startswith("version"):
            print(f"  {line}")
    print()
    print("__init__.py:")
    for line in INIT_FILE.read_text().splitlines():
        if "__version__" in line or "__tag__" in line:
            print(f"  {line}")


if __name__ == "__main__":
    main()
