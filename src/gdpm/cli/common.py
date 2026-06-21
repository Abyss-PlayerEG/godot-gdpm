"""Shared CLI utilities."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

console = Console()

CONFIG_FILENAME = "gdproject.toml"
LOCK_FILENAME = "gdpm.lock"


def find_project_root() -> Path:
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / CONFIG_FILENAME).exists():
            return parent
    return current


def require_project() -> Path:
    root = find_project_root()
    if not (root / CONFIG_FILENAME).exists():
        console.print(
            "[red]Error:[/red] Not a gdpm project. Run [bold]gdpm init[/bold] first."
        )
        raise SystemExit(1)
    return root
