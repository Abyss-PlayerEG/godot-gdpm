#!/usr/bin/env python3
"""Smoke test built archives (or the dev install).

Usage:
    python scripts/smoke.py                # test newest dist/ archive (this platform)
    python scripts/smoke.py --archive FILE  # test one specific archive
    python scripts/smoke.py --dev           # test source install via `uv run gdpm`

Mirrors what a user does after download: extract, run --version/--help
/--completion, and verify installer scripts carry the exec bit.
CI (build.yml) runs this same script against release archives.
"""

from __future__ import annotations

import argparse
import io
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

# Windows pipes default to cp1252 — keep ✓/✗ output printable everywhere
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).parent.parent
DIST_DIR = PROJECT_DIR / "dist"
PYPROJECT = PROJECT_DIR / "pyproject.toml"

_CHECK_FAILURES: list[str] = []


def plat_token() -> str:
    """Archive-name token for the current platform (matches scripts/build.py)."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    if system == "Windows":
        return "windows"
    return "linux"


def pyproject_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def check(ok: bool, label: str, detail: str = "") -> None:
    suffix = f"  {detail}" if detail else ""
    print(f"  {'✓' if ok else '✗'} {label}{suffix}")
    if not ok:
        _CHECK_FAILURES.append(label)


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    """Run a command from the project root; return (exit code, combined output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, cwd=PROJECT_DIR
        )
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    return result.returncode, result.stdout + result.stderr


def version_core(version: str) -> str:
    """Leading x.y.z of a PEP 440 version or a `v0.1.1 [dev2]` display string."""
    match = re.search(r"v?(\d+\.\d+\.\d+)", version)
    return match.group(1) if match else version


def run_cli_checks(cmd: list[str], pyver: str) -> None:
    """Assertions shared by archive mode and dev mode (cmd = how to invoke gdpm)."""
    rc, out = run_cmd([*cmd, "--version"])
    first_line = out.strip().splitlines()[0] if out.strip() else ""
    check(rc == 0 and bool(first_line), "--version", first_line)

    binary_core = version_core(first_line.split()[1]) if first_line else ""
    check(
        bool(binary_core) and version_core(pyver) == binary_core,
        "version matches pyproject",
        f"pyproject={pyver}",
    )

    rc, out = run_cmd([*cmd, "--help"])
    check(rc == 0 and "Usage" in out, "--help")

    rc, out = run_cmd([*cmd, "--completion", "zsh"])
    check(rc == 0 and out.lstrip().startswith("#compdef"), "--completion zsh")


def smoke_archive(archive: Path, pyver: str) -> None:
    shown = (
        archive.relative_to(PROJECT_DIR)
        if archive.is_relative_to(PROJECT_DIR)
        else archive
    )
    print(f"\nArchive: {shown}")
    check(archive.is_file(), "archive exists")
    if not archive.is_file():
        return

    is_windows = plat_token() == "windows"
    binary_name = "gdpm.exe" if is_windows else "gdpm"
    installer_names = (
        ("install.bat", "uninstall.bat")
        if is_windows
        else (
            "install.sh",
            "uninstall.sh",
        )
    )

    with tempfile.TemporaryDirectory(prefix="gdpm-smoke-") as tmp:
        try:
            if archive.suffix == ".zip":
                with zipfile.ZipFile(archive) as bundle:
                    bundle.extractall(tmp)
            else:
                with tarfile.open(archive) as bundle:
                    bundle.extractall(tmp, filter="data")
            check(True, "extracts cleanly")
        except (OSError, tarfile.TarError, zipfile.BadZipFile) as exc:
            check(False, "extracts cleanly", str(exc))
            return

        root = Path(tmp) / "gdpm"
        binary = root / binary_name
        check(root.is_dir() and binary.exists(), f"layout has {binary_name}")

        for name in installer_names:
            script = root / name
            present = script.is_file()
            check(present, f"{name} present")
            if present and not is_windows:
                check(os.access(script, os.X_OK), f"{name} exec bit")

        if not is_windows and binary.exists():
            check(os.access(binary, os.X_OK), "binary exec bit")

        if binary.exists():
            run_cli_checks([str(binary)], pyver)


def smoke_dev(pyver: str) -> None:
    print("\nDev install (uv run gdpm):")
    if shutil.which("uv") is None:
        check(False, "uv available", "not found in PATH")
        return
    run_cli_checks(["uv", "run", "gdpm"], pyver)


def main() -> int:
    _CHECK_FAILURES.clear()
    parser = argparse.ArgumentParser(
        description="Smoke test gdpm archives or dev install"
    )
    parser.add_argument("--archive", default="", help="test one specific archive file")
    parser.add_argument(
        "--dev", action="store_true", help="test source install via uv run gdpm"
    )
    args = parser.parse_args()

    pyver = pyproject_version()
    print(f"pyproject version: {pyver}")

    if args.dev:
        smoke_dev(pyver)
    elif args.archive:
        archive = Path(args.archive)
        if not archive.exists():
            print(f"Archive not found: {args.archive}")
            return 1
        smoke_archive(archive, pyver)
    else:
        all_archives = sorted(
            DIST_DIR.glob("gdpm_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        token = f"_{plat_token()}_"
        archives = [p for p in all_archives if token in p.name]
        if not archives:
            print(f"\nNo {plat_token()} archive in dist/ — build first:")
            print("  python3 scripts/build.py")
            print("Or test the source install:")
            print("  python3 scripts/smoke.py --dev")
            return 1
        if len(all_archives) > 1:
            extra = len(all_archives) - 1
            print(f"({extra} other archive(s) in dist/, testing newest)")
        smoke_archive(archives[0], pyver)

    print()
    if _CHECK_FAILURES:
        print(f"  {len(_CHECK_FAILURES)} smoke check(s) FAILED")
        return 1
    print("  All smoke checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
