"""gdpm godot command - Godot engine management."""

from __future__ import annotations

from pathlib import Path

import click
import httpx
from rich.console import Console
from rich.table import Table

from gdpm.cli.app import GdpmCommand, GdpmGroup
from gdpm.constants import GODOT_RELEASES_URL

console = Console()


def _get_engines_dir() -> Path:
    """Get the global engines directory."""
    engines_dir = Path.home() / ".gdpm" / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    return engines_dir


@click.group(cls=GdpmGroup, examples=[
    ("gdpm godot list", "List installed Godot versions"),
    ("gdpm godot list --remote", "List available versions"),
    ("gdpm godot install 4.7", "Install Godot 4.7"),
])
def godot() -> None:
    """Manage Godot engine versions."""


@godot.command(
    name="list",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot list", "List installed versions"),
        ("gdpm godot list --remote", "List available versions"),
    ],
)
@click.option(
    "--remote", "-r", is_flag=True,
    help="List available versions from GitHub",
)
@click.option("--limit", "-n", default=20, help="Number of remote versions to show")
def godot_list(remote: bool, limit: int) -> None:
    """List Godot engine versions."""
    if remote:
        _list_remote(limit)
    else:
        _list_local()


def _list_local() -> None:
    """List installed Godot versions."""
    engines_dir = _get_engines_dir()

    versions = []
    for d in sorted(engines_dir.iterdir()):
        if d.is_dir():
            # Check if it has a Godot binary
            has_binary = any(d.iterdir())
            versions.append((d.name, has_binary))

    if not versions:
        console.print("[dim]No Godot versions installed.[/dim]")
        console.print("  Use [bold]gdpm godot install <version>[/bold] to install.")
        return

    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=None,
    )
    table.add_column("Version", style="cyan", min_width=15)
    table.add_column("Status", min_width=10)

    for ver, has_binary in versions:
        status = (
            "[green]✓ Installed[/green]"
            if has_binary else "[red]✗ Incomplete[/red]"
        )
        table.add_row(ver, status)

    console.print(table)


def _list_remote(limit: int) -> None:
    """List available Godot versions from GitHub."""
    try:
        resp = httpx.get(
            f"{GODOT_RELEASES_URL}?per_page={limit}",
            timeout=10,
            verify=False,
        )
        resp.raise_for_status()
        releases = resp.json()
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to fetch releases: {e}")
        return

    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=None,
    )
    table.add_column("Version", style="cyan", min_width=20)
    table.add_column("Type", min_width=10)
    table.add_column("Date", min_width=12)

    for r in releases:
        tag = r.get("tag_name", "")
        pre = r.get("prerelease", False)
        date = r.get("published_at", "")[:10]

        # Only show Godot 3.x, 4.x and 5.x
        if not tag.startswith(("3.", "4.", "5.")):
            continue

        ver_type = "[yellow]Pre-release[/yellow]" if pre else "[green]Stable[/green]"
        table.add_row(tag, ver_type, date)

    console.print(table)
