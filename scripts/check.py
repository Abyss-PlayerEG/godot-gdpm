#!/usr/bin/env python3
"""Code quality check script for gdpm.

Usage:
    python scripts/check.py          # Run all checks
    python scripts/check.py mypy     # Run mypy only
    python scripts/check.py ruff     # Run ruff only
    python scripts/check.py format   # Check formatting only
    python scripts/check.py vulture  # Run vulture only
    python scripts/check.py deptry   # Run deptry only
    python scripts/check.py fix      # Auto-fix issues
"""

from __future__ import annotations

import subprocess
import sys
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
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}\n")


def check_mypy() -> bool:
    """Run mypy type checker."""
    header("mypy (type checking)")
    return run(["uv", "run", "mypy", "src/"]) == 0


def check_ruff() -> bool:
    """Run ruff linter."""
    header("ruff (linting)")
    return run(["uv", "run", "ruff", "check", "src/"]) == 0


def check_format() -> bool:
    """Check code formatting."""
    header("ruff format (formatting)")
    return run(["uv", "run", "ruff", "format", "--check", "src/"]) == 0


def check_vulture() -> bool:
    """Run vulture dead code detector."""
    header("vulture (dead code)")
    whitelist = PROJECT_DIR / ".vulture_whitelist.py"
    cmd = [
        "uv", "run", "vulture",
        str(SRC_DIR),
        str(whitelist) if whitelist.exists() else "",
        "--min-confidence", "80",
    ]
    cmd = [c for c in cmd if c]  # Remove empty strings
    return run(cmd) == 0


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
            "format": check_format,
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

    results["mypy"] = check_mypy()
    results["ruff"] = check_ruff()
    results["format"] = check_format()
    results["vulture"] = check_vulture()
    results["deptry"] = check_deptry()

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
