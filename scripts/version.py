#!/usr/bin/env python3
"""Version management script for gdpm.

Usage:
    python scripts/version.py --help             # Usage & tag table
    python scripts/version.py                    # Interactive mode
    python scripts/version.py 0.0.3              # Update version only (keeps tag)
    python scripts/version.py 0.0.3 beta         # Update version + tag
    python scripts/version.py 0.0.3 ""           # Update version, clear tag (stable)
    python scripts/version.py 0.0.3 beta-2       # Update version + tag with number

Supported tags (PyPI compatible):
    ""        -> 0.0.3        (stable)
    "dev"     -> 0.0.3.dev1   (development)
    "alpha"   -> 0.0.3a1      (alpha)
    "beta"    -> 0.0.3b1      (beta)
    "rc"      -> 0.0.3rc1     (release candidate)
    "beta-2"  -> 0.0.3b2      (beta 2)
    "rc3"     -> 0.0.3rc3     (rc 3)
"""

from __future__ import annotations

import argparse
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
    "dev": "{version}.dev{n}",
    "alpha": "{version}a{n}",
    "beta": "{version}b{n}",
    "rc": "{version}rc{n}",
}


def parse_tag(tag_input: str) -> tuple[str, int]:
    """Parse tag input like 'beta-2' or 'beta2' into (tag_name, number).

    Returns:
        (tag_name, number) e.g. ("beta", 2)
    """
    if not tag_input:
        return "", 1

    # Match patterns: "beta-2", "beta2", "rc-1", "dev3"
    match = re.match(r"^([a-z]+)-?(\d+)$", tag_input)
    if match:
        return match.group(1), int(match.group(2))

    # Plain tag without number
    return tag_input, 1


def read_current() -> tuple[str, str]:
    """Read current version and tag from __init__.py."""
    content = INIT_FILE.read_text(encoding="utf-8")

    version_match = re.search(r'__version__\s*=\s*"([^"]*)"', content)
    tag_match = re.search(r'__tag__\s*=\s*"([^"]*)"', content)

    pypi_version = version_match.group(1) if version_match else "0.0.0"
    tag_name = tag_match.group(1) if tag_match else ""

    # Extract tag number from PyPI format
    # "0.1.0b12" -> tag_num=12, "0.1.0.dev3" -> tag_num=3
    tag_num = 1
    num_match = re.search(r"[a-z](\d+)$|\.dev(\d+)$|rc(\d+)$", pypi_version)
    if num_match:
        tag_num = int(next(g for g in num_match.groups() if g))

    # Extract base version
    base_version = re.sub(r"(\.dev\d+|[a-z]+\d+|rc\d+)$", "", pypi_version)

    # Reconstruct tag with number
    tag = f"{tag_name}-{tag_num}" if tag_name and tag_num > 1 else tag_name

    return base_version, tag


def get_pypi_version(version: str, tag: str) -> str:
    """Get PyPI-compatible version string."""
    tag_name, num = parse_tag(tag)
    if not tag_name:
        return version
    return TAG_FORMATS.get(tag_name, version).format(version=version, n=num)


def get_display_version(version: str, tag: str) -> str:
    """Get display version string."""
    pypi = get_pypi_version(version, tag)
    if tag:
        tag_name, num = parse_tag(tag)
        if num > 1:
            return f"{pypi} ({tag_name}{num})"
        return f"{pypi} ({tag_name})"
    return f"{pypi} (stable)"


def update_files(version: str, tag: str) -> None:
    """Update pyproject.toml and __init__.py.

    All pattern substitutions are validated BEFORE any write: a zero-match
    substitution aborts with a non-zero exit instead of silently reporting
    success or leaving a half-updated pair of files.
    """
    tag_name, _ = parse_tag(tag)
    pypi_version = get_pypi_version(version, tag)

    # Stage all rewrites first (all-or-nothing on pattern mismatch)
    new_pyproject, n_project = re.subn(
        r'^version\s*=\s*"[^"]*"',
        f'version = "{pypi_version}"',
        PYPROJECT_FILE.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    new_init = INIT_FILE.read_text(encoding="utf-8")
    new_init, n_version = re.subn(
        r'__version__\s*=\s*"[^"]*"',
        f'__version__ = "{pypi_version}"',
        new_init,
    )
    new_init, n_tag = re.subn(
        r'__tag__\s*=\s*"[^"]*"',
        f'__tag__ = "{tag_name}"',
        new_init,
    )

    if n_project == 0:
        sys.exit("Error: version pattern not found in pyproject.toml")
    if n_version == 0 or n_tag == 0:
        sys.exit("Error: __version__/__tag__ pattern not found in src/gdpm/__init__.py")

    # Patterns all matched: commit both files
    PYPROJECT_FILE.write_text(new_pyproject, encoding="utf-8")
    INIT_FILE.write_text(new_init, encoding="utf-8")


def validate_version(version: str) -> bool:
    """Validate version format (x.y.z)."""
    return bool(re.match(r"^\d+\.\d+\.\d+$", version))


def validate_tag(tag_input: str) -> bool:
    """Validate tag input like 'beta', 'beta-2', 'rc1'."""
    if not tag_input:
        return True
    tag_name, _ = parse_tag(tag_input)
    return tag_name in VALID_TAGS


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser (--help doubles as the usage doc)."""
    parser = argparse.ArgumentParser(
        prog="python scripts/version.py",
        description=(
            "Update the gdpm version in pyproject.toml and src/gdpm/__init__.py. "
            "Omit all arguments for interactive mode."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Tags (PyPI compatible):\n"
            "  (empty)  -> 0.0.3        stable\n"
            "  dev      -> 0.0.3.dev1\n"
            "  alpha    -> 0.0.3a1\n"
            "  beta     -> 0.0.3b1\n"
            "  rc       -> 0.0.3rc1\n"
            "  beta-2   -> 0.0.3b2      also accepts beta2\n"
            "  rc3      -> 0.0.3rc3\n"
        ),
    )
    parser.add_argument(
        "version",
        nargs="?",
        metavar="VERSION",
        help="new version in x.y.z form; omit for interactive mode",
    )
    parser.add_argument(
        "tag",
        nargs="?",
        metavar="TAG",
        default=None,
        help="dev/alpha/beta/rc with optional number (beta-2); "
        'omit to keep the current tag, pass "" for stable',
    )
    return parser


def _run_interactive(current_version: str, current_tag: str) -> int:
    """Interactive mode: prompt for version and tag, return exit code."""
    print(f"Current version: {get_display_version(current_version, current_tag)}")
    print()

    new_version = input("New version (empty to skip): ").strip()
    if not new_version:
        print("No changes.")
        return 0
    if not validate_version(new_version):
        print(f"Error: Invalid version format '{new_version}'. Use x.y.z")
        return 1

    print(f"Tags: {', '.join(VALID_TAGS)} (empty = stable)")
    new_tag = input("Tag (empty = stable): ").strip().lower()

    if not validate_tag(new_tag):
        print(f"Error: Invalid tag '{new_tag}'")
        return 1

    update_files(new_version, new_tag)
    _print_result(current_version, current_tag, new_version, new_tag)
    return 0


def _run_cli(
    version_arg: str, tag_arg: str | None, current_version: str, current_tag: str
) -> int:
    """Command-line mode: validate, update, return exit code."""
    version = version_arg.strip()
    if not validate_version(version):
        print(f"Error: Invalid version format '{version}'. Use x.y.z")
        return 1

    # No tag argument -> keep current tag (update version only);
    # explicit "" means stable
    tag = current_tag if tag_arg is None else tag_arg.strip().lower()
    if not validate_tag(tag):
        print(f"Error: Invalid tag '{tag}'. Use: {', '.join(VALID_TAGS)}")
        return 1
    if tag_arg is None and current_tag:
        print(f'Note: keeping current tag "{current_tag}" (pass "" for stable)')

    update_files(version, tag)
    _print_result(current_version, current_tag, version, tag)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point: dispatch interactive/CLI mode, return exit code."""
    args = build_parser().parse_args(argv)
    current_version, current_tag = read_current()

    if args.version is None:
        return _run_interactive(current_version, current_tag)
    return _run_cli(args.version, args.tag, current_version, current_tag)


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
    sys.exit(main())
