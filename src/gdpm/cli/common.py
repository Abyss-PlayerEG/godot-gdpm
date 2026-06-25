"""Shared CLI utilities."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

console = Console()

CONFIG_FILENAME = "gdproject.toml"
LOCK_FILENAME = "gdpm.lock"

TEMPLATE_TAGS = {
    "template",
    "starter kit",
    "starterkit",
    "demo",
    "project",
    "boilerplate",
    "sample",
}


def print_out(*args: object, **kwargs: object) -> None:
    """Print with empty lines before and after."""
    console.print()
    console.print(*args, **kwargs)
    console.print()


def is_template(tags: list[str]) -> bool:
    normalized = {t.lower().replace(" ", "") for t in tags}
    return bool(normalized & TEMPLATE_TAGS)


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
