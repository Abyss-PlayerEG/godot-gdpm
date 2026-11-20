#!/usr/bin/env python3
"""Reset the project virtual environment (.venv).

Usage:
    python scripts/env.py              # Interactive: clear env, ask to reinstall
    python scripts/env.py --yes        # Clear env + reinstall without prompting
    python scripts/env.py --yes --refresh  # ... and bypass cache (re-download)
    python scripts/env.py --status     # Show environment status only
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
VENV_DIR = PROJECT_DIR / ".venv"


def human_size(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def venv_python() -> Path | None:
    if sys.platform == "win32":
        candidate = VENV_DIR / "Scripts" / "python.exe"
    else:
        candidate = VENV_DIR / "bin" / "python"
    return candidate if candidate.exists() else None


def count_packages() -> int:
    patterns = (
        "lib/python*/site-packages/*.dist-info",
        "Lib/site-packages/*.dist-info",
    )
    return sum(len(list(VENV_DIR.glob(p))) for p in patterns)


def show_status() -> None:
    print("Environment status:")
    if not VENV_DIR.exists():
        print("  .venv:   not found")
        return

    total = sum(f.stat().st_size for f in VENV_DIR.rglob("*") if f.is_file())
    print(f"  .venv:   {VENV_DIR} ({human_size(total)}, {count_packages()} packages)")

    python = venv_python()
    if python is None:
        print("  Python:  executable missing")
        print("  Health:  broken")
        return

    result = subprocess.run(
        [str(python), "-c", "import gdpm"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    version = subprocess.run(
        [str(python), "-V"], capture_output=True, text=True, check=False
    ).stdout.strip()
    print(f"  Python:  {version}")
    if result.returncode == 0:
        print("  Health:  healthy")
    else:
        print("  Health:  broken (gdpm not importable)")


def remove_venv() -> bool:
    if not VENV_DIR.exists():
        print("  Nothing to clear (.venv not found).")
        return False
    print(f"  Removing {VENV_DIR} ...")
    try:
        shutil.rmtree(VENV_DIR)
    except OSError as exc:
        print(f"  Failed to remove .venv: {exc}")
        if sys.platform == "win32":
            print("  (on Windows, close processes using .venv and retry)")
        return False
    print("  Cleared .venv")
    return True


def sync(refresh: bool) -> int:
    if shutil.which("uv") is None:
        print("  uv not found in PATH. Install it first: https://docs.astral.sh/uv/")
        return 1
    cmd = ["uv", "sync", *(["--refresh"] if refresh else [])]
    print(f"  Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=PROJECT_DIR, check=False).returncode


def confirm(prompt: str, default: bool = False) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    answer = input(f"  {prompt} {hint} ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset the project virtual environment"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="clear env and reinstall without prompting",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="bypass uv cache and re-download packages (with --yes)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="show environment status only",
    )
    args = parser.parse_args()

    show_status()
    if args.status:
        return 0

    if args.yes:
        print()
        if not remove_venv():
            return 1
        print()
        return sync(refresh=args.refresh)

    print()
    if not confirm("Clear the current environment (.venv)?"):
        print("Cancelled.")
        return 0
    print()
    if not remove_venv():
        return 1

    print()
    answer = (
        input("  Reinstall dependencies? [Y]es (use cache) / [r]e-download / [n]o: ")
        .strip()
        .lower()
    )
    if answer in ("n", "no"):
        print("  Skipped. Run `uv sync` later to reinstall.")
        return 0
    if answer in ("r", "re-download", "redownload"):
        return sync(refresh=True)
    return sync(refresh=False)


if __name__ == "__main__":
    sys.exit(main())
