#!/usr/bin/env python3
"""Clean build artifacts and caches."""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent

# Directories to remove (regenerable junk only)
#
# Never add here:
#   .venv/                 -> owned by scripts/env.py
#   .idea/ .vscode/        -> live IDE config, deleting disrupts the editor
#   .vulture_whitelist.py  -> tracked source file (despite the .gitignore line)
#   gdpm-local/            -> committed data (packed local plugins)
DIRS = [
    "dist",
    "build",
    "wheels",
    "coverage-report",
    "htmlcov",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".pylint.d",
    ".deptry",
    "__pycache__",
]

# File patterns to remove
PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    "*.spec",
    ".coverage",
    ".coverage.*",
    "coverage.xml",
    "*.swp",
    "*.swo",
    ".DS_Store",
    "Thumbs.db",
]


def clean() -> None:
    """Remove build artifacts and caches."""
    removed = 0
    exclude = {".venv", ".git", "node_modules"}

    # Remove directories
    for name in DIRS:
        for path in PROJECT_DIR.rglob(name):
            if path.is_dir() and not any(ex in path.parts for ex in exclude):
                shutil.rmtree(path, ignore_errors=True)
                print(f"  Removed: {path.relative_to(PROJECT_DIR)}")
                removed += 1

    # Remove files matching patterns
    for pattern in PATTERNS:
        for path in PROJECT_DIR.rglob(pattern):
            if any(ex in path.parts for ex in exclude):
                continue
            if path.is_file():
                path.unlink(missing_ok=True)
                print(f"  Removed: {path.relative_to(PROJECT_DIR)}")
                removed += 1
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                print(f"  Removed: {path.relative_to(PROJECT_DIR)}")
                removed += 1

    if removed == 0:
        print("Nothing to clean.")
    else:
        print(f"\nCleaned {removed} items.")


if __name__ == "__main__":
    print("Cleaning build artifacts...\n")
    clean()
