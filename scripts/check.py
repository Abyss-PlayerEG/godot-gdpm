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

import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
SRC_DIR = PROJECT_DIR / "src"

CHECKS = [
    "mypy",
    "ruff",
    "pylint",
    "legacy",
    "vulture",
    "deptry",
]


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


def check_mypy() -> bool:
    """Run mypy type checker."""
    header("mypy (type checking)")
    result = run(["uv", "run", "mypy", "src/"])
    if result != 0:
        print("  Note: mypy may fail due to pathspec/Python 3.14 compatibility issue")
    return result == 0


def check_ruff() -> bool:
    """Run ruff linter."""
    header("ruff (linting)")
    return run(["uv", "run", "ruff", "check", "src/"]) == 0


def check_format() -> bool:
    """Check code formatting."""
    header("ruff format (formatting)")
    return run(["uv", "run", "ruff", "format", "--check", "src/"]) == 0


def check_pylint() -> bool:
    """Run pylint static analysis."""
    header("pylint (static analysis)")
    return run(["uv", "run", "pylint", "src/gdpm/"]) == 0


def check_vulture() -> bool:
    """Run vulture dead code detector."""
    header("vulture (dead code)")
    whitelist = PROJECT_DIR / ".vulture_whitelist.py"
    cmd = [
        "uv",
        "run",
        "vulture",
        str(SRC_DIR),
        str(whitelist) if whitelist.exists() else "",
        "--min-confidence",
        "80",
    ]
    cmd = [c for c in cmd if c]
    return run(cmd) == 0


def check_legacy_syntax() -> bool:
    """Check for legacy Python 2 syntax patterns."""
    header("legacy syntax check")
    import re

    pattern = re.compile(r"except\s+\w+\s*,\s*\w+\s*:")
    found = False
    for py_file in SRC_DIR.rglob("*.py"):
        for i, line in enumerate(py_file.read_text().splitlines(), 1):
            if pattern.search(line):
                print(f"  {py_file}:{i}: {line.strip()}")
                found = True
    if found:
        print("\n  Use 'except (A, B):' or 'except A as B:' instead of 'except A, B:'")
        return False
    print("  No legacy syntax found.")
    return True


def check_deptry() -> bool:
    """Run deptry dependency checker."""
    header("deptry (dependencies)")
    return run(["uv", "run", "deptry", "."]) == 0


def check_test() -> bool:
    """Run pytest."""
    header("pytest (tests)")
    return run(["uv", "run", "pytest", "tests/", "-v"]) == 0


def fix() -> None:
    """Auto-fix issues."""
    header("Auto-fixing issues")

    print("Running ruff fix...")
    run(["uv", "run", "ruff", "check", "src/", "--fix"])

    print("\nRunning ruff format...")
    run(["uv", "run", "ruff", "format", "src/"])

    print("\nDone. Run 'python scripts/check.py' to verify.")


def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        commands = {
            "mypy": check_mypy,
            "ruff": check_ruff,
            "pylint": check_pylint,
            "legacy": check_legacy_syntax,
            "vulture": check_vulture,
            "deptry": check_deptry,
            "test": check_test,
            "fix": fix,
        }

        if cmd in commands:
            if cmd == "fix":
                fix()
            else:
                success = commands[cmd]()
                sys.exit(0 if success else 1)
        else:
            print(f"Unknown command: {cmd}")
            print(f"Available: {', '.join(commands.keys())}")
            sys.exit(1)
        return

    # Run all checks
    results = {}
    for name in CHECKS:
        func = {
            "mypy": check_mypy,
            "ruff": check_ruff,
            "pylint": check_pylint,
            "legacy": check_legacy_syntax,
            "vulture": check_vulture,
            "deptry": check_deptry,
        }[name]
        results[name] = func()

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
