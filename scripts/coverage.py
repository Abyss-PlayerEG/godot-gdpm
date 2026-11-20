#!/usr/bin/env python3
"""pytest coverage report for gdpm.

Usage:
    python scripts/coverage.py                 # run tests with coverage, print report
    python scripts/coverage.py --weak 15       # weakest files to list (default 10)
    python scripts/coverage.py --fail-under 45 # exit 1 below threshold (gate mode)
    python scripts/coverage.py --html          # also write htmlcov/ (gitignored)
    python scripts/coverage.py --lcov          # also write lcov.info (editor gutters)
    python scripts/coverage.py --xml           # also write coverage.xml (CI/Cobertura)
    python scripts/coverage.py --from-json coverage-report/coverage.json \
        --markdown "$GITHUB_STEP_SUMMARY"      # render an existing report (no re-run)

Tests run through pytest-cov (dev dependency); the same gate is enforced
by scripts/check.py. All artifacts (data file, JSON, HTML, LCOV, XML) land
in coverage-report/ (gitignored).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
COV_SOURCE = "src/gdpm"
REPORT_DIR = PROJECT_DIR / "coverage-report"


@dataclass
class FileCov:
    """Coverage of one source file."""

    path: str
    pct: float
    stmts: int
    miss: int


@dataclass
class Report:
    """Aggregated coverage numbers."""

    total_pct: float
    stmts: int
    covered: int
    layers: dict[str, tuple[int, int]]
    files: list[FileCov]


def run(cmd: list[str], env: dict[str, str] | None = None) -> int:
    """Run a command from the project root and return its exit code."""
    try:
        result = subprocess.run(cmd, cwd=PROJECT_DIR, env=env, check=False)
    except FileNotFoundError:
        print(f"  Command not found: {cmd[0]!r} (is it installed and on PATH?)")
        return 127
    return result.returncode


def layer_of(file_path: str) -> str:
    """Group a source path into its architectural layer."""
    parts = file_path.split("/")
    if len(parts) < 3:
        return "(other)"
    name = parts[2]
    if name.endswith(".py"):
        return "(top-level)"
    if name == "cli" and len(parts) > 4:
        return "cli/commands"
    return name


def parse_report(json_path: Path) -> Report:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    totals = data["totals"]
    layers: dict[str, tuple[int, int]] = {}
    files: list[FileCov] = []

    for path, info in data["files"].items():
        summary = info["summary"]
        stmts = int(summary["num_statements"])
        miss = int(summary["missing_lines"])
        pct = float(summary["percent_covered"])
        key = layer_of(str(path))
        old_stmts, old_miss = layers.get(key, (0, 0))
        layers[key] = (old_stmts + stmts, old_miss + miss)
        files.append(FileCov(str(path), pct, stmts, miss))

    return Report(
        total_pct=float(totals["percent_covered"]),
        stmts=int(totals["num_statements"]),
        covered=int(totals["covered_lines"]),
        layers=layers,
        files=files,
    )


def render_markdown(report: Report, weak_count: int) -> str:
    """Render the same summary as a markdown block (for CI job summaries)."""
    lines = [
        f"## Coverage: {report.total_pct:.0f}% "
        f"({report.covered}/{report.stmts} statements)",
        "",
        "| Layer | Stmts | Miss | Cover |",
        "|---|---:|---:|---:|",
    ]
    ordered = sorted(
        report.layers.items(),
        key=lambda item: (item[1][0] - item[1][1]) / item[1][0],
    )
    for key, (stmts, miss) in ordered:
        pct = 100 * (stmts - miss) / stmts
        lines.append(f"| `{key}` | {stmts} | {miss} | {pct:.0f}% |")

    if weak_count > 0:
        lines.extend(
            [
                "",
                f"### Weakest {weak_count} files",
                "",
                "| File | Cover | Miss |",
                "|---|---:|---:|",
            ]
        )
        weakest = sorted(report.files, key=lambda f: (f.pct, -f.miss))
        for entry in weakest[:weak_count]:
            short = entry.path.removeprefix("src/gdpm/")
            lines.append(
                f"| `{short}` | {entry.pct:.0f}% | {entry.miss}/{entry.stmts} |"
            )

    return "\n".join(lines) + "\n"


def print_report(report: Report, weak_count: int) -> None:
    print(
        f"\nCoverage: {report.total_pct:.0f}%  "
        f"({report.covered}/{report.stmts} statements)"
    )

    print("\nBy layer:")
    print(f"  {'layer':<16}{'stmts':>6}{'miss':>7}{'cov':>7}")
    ordered = sorted(
        report.layers.items(),
        key=lambda item: (item[1][0] - item[1][1]) / item[1][0],
    )
    for key, (stmts, miss) in ordered:
        pct = 100 * (stmts - miss) / stmts
        print(f"  {key:<16}{stmts:>6}{miss:>7}{pct:>6.0f}%")

    if weak_count > 0:
        print(f"\nWeakest {weak_count} files:")
        weakest = sorted(report.files, key=lambda f: (f.pct, -f.miss))
        for entry in weakest[:weak_count]:
            short = entry.path.removeprefix("src/gdpm/")
            print(f"  {entry.pct:>5.0f}%  {short:<40} {entry.miss}/{entry.stmts} miss")


def main() -> int:
    parser = argparse.ArgumentParser(description="pytest coverage report for gdpm")
    parser.add_argument(
        "--weak", type=int, default=10, help="number of weakest files to list"
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=None,
        metavar="PCT",
        help="exit 1 if total coverage is below PCT",
    )
    parser.add_argument(
        "--html", action="store_true", help="also write htmlcov/ (gitignored)"
    )
    parser.add_argument(
        "--lcov",
        action="store_true",
        help="also write lcov.info (VSCode coverage gutters / Coveralls)",
    )
    parser.add_argument(
        "--xml",
        action="store_true",
        help="also write coverage.xml (Cobertura, CI dashboards)",
    )
    parser.add_argument(
        "--from-json",
        default="",
        metavar="PATH",
        help="render an existing coverage.json without running tests",
    )
    parser.add_argument(
        "--markdown",
        default="",
        metavar="PATH",
        help="append a markdown summary to PATH (e.g. GITHUB_STEP_SUMMARY)",
    )
    args = parser.parse_args()

    REPORT_DIR.mkdir(exist_ok=True)
    json_path = Path(args.from_json) if args.from_json else REPORT_DIR / "coverage.json"

    if args.from_json:
        if not json_path.exists():
            print(f"Coverage JSON not found: {json_path}")
            return 1
        report = parse_report(json_path)
        rc = 0
    else:
        env = os.environ.copy()
        env["COVERAGE_FILE"] = str(REPORT_DIR / ".coverage")

        cmd = [
            "uv",
            "run",
            "pytest",
            "tests/",
            "-q",
            f"--cov={COV_SOURCE}",
            f"--cov-report=json:{json_path}",
        ]
        if args.html:
            cmd.append(f"--cov-report=html:{REPORT_DIR / 'html'}")
        if args.lcov:
            cmd.append(f"--cov-report=lcov:{REPORT_DIR / 'lcov.info'}")
        if args.xml:
            cmd.append(f"--cov-report=xml:{REPORT_DIR / 'coverage.xml'}")

        print("Running tests with coverage...")
        rc = run(cmd, env=env)

        if not json_path.exists():
            print("No coverage data produced (pytest failed before reporting?).")
            return rc or 1
        report = parse_report(json_path)

    print_report(report, args.weak)

    if args.markdown:
        with open(args.markdown, "a", encoding="utf-8") as handle:
            handle.write(render_markdown(report, args.weak))
        print(f"\nMarkdown summary appended to {args.markdown}")

    if not args.from_json:
        print("\nReports in coverage-report/ (gitignored):")
        print("  coverage.json  coverage-report/.coverage")
        if args.html:
            print("  html           coverage-report/html/index.html")
        if args.lcov:
            print("  lcov.info      coverage-report/lcov.info")
        if args.xml:
            print("  coverage.xml   coverage-report/coverage.xml")

    if rc != 0:
        print("\nTests failed — see pytest output above.")
        return rc
    if args.fail_under is not None and report.total_pct < args.fail_under:
        print(f"\nCoverage {report.total_pct:.1f}% < threshold {args.fail_under}%")
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
