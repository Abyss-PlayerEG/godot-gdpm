"""gdpm list command."""

from __future__ import annotations

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.utils.tag import scan_addons

console = Console()


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm list", "List all installed plugins"),
        ("gdpm list --json", "Output as JSON"),
    ],
)
@click.option("--outdated", is_flag=True, help="Show only outdated plugins")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_cmd(outdated: bool, as_json: bool) -> None:
    """List installed plugins."""
    root = require_project()
    config = read_project_config(root / "gdproject.toml")
    addons_dir = root / config.addons_dir
    lock_entries = {e.name: e for e in read_lockfile(find_lockfile(root))}

    installed: list[dict[str, str]] = []

    for addon_path, tag in scan_addons(addons_dir):
        locked = lock_entries.get(tag.slug)
        version = "local" if tag.is_local else (locked.version if locked else "?")

        installed.append(
            {
                "name": addon_path.name,
                "slug": tag.slug,
                "version": version,
                "source": tag.source,
            }
        )

    if as_json:
        import json

        click.echo(json.dumps(installed, indent=2))
        return

    if not installed:
        console.print("[dim]No plugins installed.[/dim]")
        console.print("  Use [bold]gdpm add <plugin>[/bold] to install plugins.")
        return

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )
    table.add_column("Plugin", style="cyan", min_width=20)
    table.add_column("Version", style="green", min_width=10)
    table.add_column("Source", style="dim")

    for p in installed:
        version = p["version"]
        if version == "local":
            version = f"[yellow]{version}[/yellow]"
        table.add_row(p["name"], version, p["source"])

    console.print()
    console.print(
        Panel(
            table,
            title=f"[bold cyan]Installed Plugins ({len(installed)})[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )
    console.print()
