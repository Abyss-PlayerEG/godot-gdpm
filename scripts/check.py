#!/usr/bin/env python3
"""Code quality check script for gdpm.

Usage:
    python scripts/check.py            # Run all checks
    python scripts/check.py <check>    # Run a single check
    python scripts/check.py fix        # Auto-fix lint & format issues
    python scripts/check.py --help     # Show this help

Checks: mypy ruff format pylint vulture deptry test (pytest + coverage gate)
        zizmor (GitHub Actions workflow security; --min-severity=low so
        informational style suggestions don't block, real findings do)
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# Windows pipes default to cp1252 — keep ✓/✗ output printable everywhere
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).parent.parent
SRC_DIR = PROJECT_DIR / "src"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
TESTS_DIR = PROJECT_DIR / "tests"
REPORT_DIR = PROJECT_DIR / "coverage-report"
COVERAGE_MIN = 45


def run(cmd: list[str]) -> int:
    """Run a command from the project root and return its exit code."""
    try:
        result = subprocess.run(cmd, cwd=PROJECT_DIR, check=False)
    except FileNotFoundError:
        print(f"  Command not found: {cmd[0]!r} (is it installed and on PATH?)")
        return 127
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
    paths = [str(SRC_DIR), str(SCRIPTS_DIR)]
    whitelist = PROJECT_DIR / ".vulture_whitelist.py"
    if whitelist.exists():
        paths.append(str(whitelist))
    return run(["uv", "run", "vulture", "--min-confidence", "80", *paths]) == 0


def check_test() -> bool:
    """Run pytest with the coverage gate."""
    header(f"pytest (tests + coverage ≥{COVERAGE_MIN}%)")
    if not TESTS_DIR.exists():
        print("  No tests directory found, skipping.")
        return True
    # pytest exits 5 (failure) when no tests are collected — skip instead
    if not list(TESTS_DIR.rglob("test_*.py")):
        print("  No test files found, skipping.")
        return True
    REPORT_DIR.mkdir(exist_ok=True)
    return (
        run(
            [
                "uv",
                "run",
                "pytest",
                "tests/",
                "-v",
                f"--cov={SRC_DIR.name}/gdpm",
                f"--cov-fail-under={COVERAGE_MIN}",
                "--cov-report=term",
                f"--cov-report=json:{REPORT_DIR / 'coverage.json'}",
            ]
        )
        == 0
    )


def fix() -> bool:
    """Auto-fix lint & format issues (whole repo)."""
    header("Auto-fixing issues")

    print("Running ruff fix...")
    rc1 = run(["uv", "run", "ruff", "check", "--fix"])

    print("\nRunning ruff format...")
    rc2 = run(["uv", "run", "ruff", "format"])

    if rc1 or rc2:
        print("\nFix incomplete (unfixable issues or command error — see above).")
        print("Run 'python scripts/check.py' for details.")
        return False
    print("\nDone. Run 'python scripts/check.py' to verify.")
    return True


CHECKS: dict[str, Callable[[], bool]] = {
    "mypy": lambda: _run(
        "mypy (type checking)", ["uv", "run", "mypy", "src/", "scripts/"]
    ),
    "ruff": lambda: _run("ruff (linting)", ["uv", "run", "ruff", "check"]),
    "format": lambda: _run(
        "ruff format (formatting)", ["uv", "run", "ruff", "format", "--check"]
    ),
    "pylint": lambda: _run(
        "pylint (static analysis)",
        ["uv", "run", "pylint", "src/", "scripts/", "tests/"],
    ),
    "vulture": check_vulture,
    "deptry": lambda: _run("deptry (dependencies)", ["uv", "run", "deptry", "."]),
    "test": check_test,
    # --min-severity=low: informational findings are style suggestions and
    # must not block; low and above fail the gate. Policy and ignore list
    # live in .github/zizmor.yml (see notes/todo/CI工作流优化.md, batch C2).
    "zizmor": lambda: _run(
        "zizmor (workflow security)",
        ["uv", "run", "zizmor", "--min-severity=low", ".github/workflows/"],
    ),
}
COMMANDS: dict[str, Callable[[], bool]] = {**CHECKS, "fix": fix}


def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd in ("-h", "--help"):
            print(__doc__)
            return

        if cmd not in COMMANDS:
            print(f"Unknown command: {cmd}")
            print(f"Available: {', '.join(COMMANDS)}")
            sys.exit(1)

        sys.exit(0 if COMMANDS[cmd]() else 1)

    # Run all checks
    results = {name: func() for name, func in CHECKS.items()}

    # Summary
    header("Summary")
    failed = [name for name, passed in results.items() if not passed]
    for name in CHECKS:
        print(f"  {'✗' if name in failed else '✓'} {name}")

    print()
    if not failed:
        print("  All checks passed!")
        return

    print(f"  Failed: {', '.join(failed)}")
    if {"ruff", "format"} & set(failed):
        print("  Lint/format issues can be auto-fixed:")
        print("    python scripts/check.py fix")
    sys.exit(1)


if __name__ == "__main__":
    main()
