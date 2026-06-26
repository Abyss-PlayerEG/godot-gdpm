"""gdpm cache command."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from gdpm.cache.file_cache import FileCache
from gdpm.cli.app import GdpmCommand, GdpmGroup
from gdpm.config.global_config import read_global_config

console = Console()


@click.group(cls=GdpmGroup, examples=[
    ("gdpm cache info", "Show cache size and location"),
    ("gdpm cache clean", "Clean all cached files"),
    ("gdpm cache clean -y", "Clean without confirmation"),
])
def cache() -> None:
    """Manage global cache."""


@cache.command(
    name="info",
    cls=GdpmCommand,
    examples=[
        ("gdpm cache info", "Show cache size and location"),
    ],
)
def cache_info() -> None:
    """Show cache information."""
    config = read_global_config()
    cache_dir = Path(config.cache_dir)
    file_cache = FileCache(cache_dir)

    size = file_cache.size()
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f} MB"

    count = 0
    for letter_dir in cache_dir.glob("downloads/*/"):
        if letter_dir.is_dir():
            count += len(list(letter_dir.glob("*.zip")))

    console.print(
        f"  Cache dir:  [cyan]{cache_dir}[/cyan]\n"
        f"  Cache size: [yellow]{size_str}[/yellow]\n"
        f"  Plugins:    [green]{count}[/green]"
    )


@cache.command(
    name="clean",
    cls=GdpmCommand,
    examples=[
        ("gdpm cache clean", "Clean all cached files"),
    ],
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def cache_clean(yes: bool) -> None:
    """Clean all cached files."""
    config = read_global_config()
    cache_dir = Path(config.cache_dir)
    file_cache = FileCache(cache_dir)

    size = file_cache.size()
    if size == 0:
        console.print("  Cache is already empty.")
        return

    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f} MB"

    if not yes:
        click.echo(f"  This will remove {size_str} of cached files.")
        if not click.confirm("  Continue?"):
            click.echo("  Cancelled.")
            return

    file_cache.clean()
    console.print(f"  [green]✓[/green] Cache cleaned ({size_str} freed)")
