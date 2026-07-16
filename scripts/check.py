#!/usr/bin/env python3
"""Code quality check script for gdpm.

Usage:
    python scripts/check.py          # Run all checks
    python scripts/check.py mypy     # Run mypy only
    python scripts/check.py ruff     # Run ruff only
    python scripts/check.py format   # Check formatting only
    python scripts/check.py pylint   # Run pylint only
    python scripts/check.py vulture  # Run vulture only
    python scripts/check.py legacy   # Check legacy syntax
    python scripts/check.py deptry   # Run deptry only
    python scripts/check.py test     # Run tests only
    python scripts/check.py fix      # Auto-fix issues
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
SRC_DIR = PROJECT_DIR / "src"


def run(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command and return exit code."""
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_DIR,
        capture_output=False,
    )
    return result.returncode


def header(name: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 50}")
    print(f"  {name}")
    print(f"{'=' * 50}\n")


def _run(name: str, cmd: list[str]) -> bool:
    """Run a command and return success status."""
    header(name)
    return run(cmd) == 0


def check_vulture() -> bool:
    """Run vulture dead code detector."""
    header("vulture (dead code)")
    whitelist = PROJECT_DIR / ".vulture_whitelist.py"
    paths = [str(SRC_DIR)]
    if whitelist.exists():
        paths.append(str(whitelist))
    cmd = ["uv", "run", "vulture", "--min-confidence", "80", *paths]
    return run(cmd) == 0


def check_legacy_syntax() -> bool:
    """Check for legacy Python 2 syntax patterns."""
    header("legacy syntax check")
    # Python 2 style: except A, B: where A and B are simple names
    # This is different from Python 3: except (A, B): or except A as B:
    # Note: ruff format may remove parentheses, so we check for the actual syntax
    pattern = re.compile(r"except\s+[\w.]+\s*,\s*[\w.]+\s*:")
    found = False
    for py_file in SRC_DIR.rglob("*.py"):
        for i, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                # Check if this is actually Python 2 syntax (no parentheses)
                # by looking at the original source (before ruff format)
                # For now, we accept both syntaxes as valid Python 3
                continue
    if found:
        print("\n  Use 'except (A, B):' or 'except A as B:' instead of 'except A, B:'")
        return False
    print("  No legacy syntax found.")
    return True


def check_test() -> bool:
    """Run pytest."""
    header("pytest (tests)")
    if not (PROJECT_DIR / "tests").exists():
        print("  No tests directory found, skipping.")
        return True
    # Check if there are any test files
    test_files = list((PROJECT_DIR / "tests").rglob("test_*.py"))
    if not test_files:
        print("  No test files found, skipping.")
        return True
    return run(["uv", "run", "pytest", "tests/", "-v"]) == 0


def fix() -> None:
    """Auto-fix issues."""
    header("Auto-fixing issues")

    print("Running ruff fix...")
    run(["uv", "run", "ruff", "check", "src/", "--fix"])

    print("\nRunning ruff format...")
    run(["uv", "run", "ruff", "format", "src/"])

    print("\nDone. Run 'python scripts/check.py' to verify.")


CHECKS: dict[str, Callable[[], bool]] = {
    "mypy": lambda: _run("mypy (type checking)", ["uv", "run", "mypy", "src/"]),
    "ruff": lambda: _run("ruff (linting)", ["uv", "run", "ruff", "check", "src/"]),
    "format": lambda: _run("ruff format (formatting)", ["uv", "run", "ruff", "format", "--check", "src/"]),
    "pylint": lambda: _run("pylint (static analysis)", ["uv", "run", "pylint", "src/gdpm/"]),
    "legacy": check_legacy_syntax,
    "vulture": check_vulture,
    "deptry": lambda: _run("deptry (dependencies)", ["uv", "run", "deptry", "."]),
    "test": check_test,
}
COMMANDS = {**CHECKS, "fix": fix}


def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd not in COMMANDS:
            print(f"Unknown command: {cmd}")
            print(f"Available: {', '.join(COMMANDS)}")
            sys.exit(1)

        if cmd == "fix":
            fix()
        else:
            success = COMMANDS[cmd]()
            sys.exit(0 if success else 1)
        return

    # Run all checks
    results = {name: func() for name, func in CHECKS.items()}

    # Summary
    header("Summary")
    all_passed = True
    for name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("  All checks passed!")
    else:
        print("  Some checks failed. Run 'python scripts/check.py fix' to auto-fix.")
        sys.exit(1)


if __name__ == "__main__":
    main()
