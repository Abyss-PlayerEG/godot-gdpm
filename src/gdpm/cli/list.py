"""gdpm list command."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile

console = Console()

TAG_FILENAME = "tag.gdpm"


@click.command()
@click.option("--outdated", is_flag=True, help="Show only outdated plugins")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_cmd(outdated: bool, as_json: bool) -> None:
    """List installed plugins."""
    root = require_project()
    config_path = root / "gdproject.toml"
    config = read_project_config(config_path)
    addons_dir = root / config.addons_dir
    lock_path = find_lockfile(root)

    lock_entries = read_lockfile(lock_path)
    lock_map = {e.name: e for e in lock_entries}

    all_deps = {**config.dependencies, **config.dev_dependencies}

    installed: list[dict[str, str]] = []

    if addons_dir.exists():
        for child in sorted(addons_dir.iterdir()):
            if not child.is_dir():
                continue

            tag_path = child / TAG_FILENAME
            if not tag_path.exists():
                continue

            tag_content = tag_path.read_text(encoding="utf-8").strip()

            slug = ""
            if "/" in tag_content:
                slug = tag_content.split("/")[-1]
            else:
                slug = tag_content.split("+")[-1]

            locked = lock_map.get(slug)
            version = locked.version if locked else "?"

            dep = all_deps.get(slug)
            source = tag_content

            installed.append(
                {
                    "slug": slug,
                    "dir_name": child.name,
                    "version": version,
                    "source": source,
                    "is_dev": str(dep.is_dev) if dep else "false",
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

    console.print(f"[bold]Installed plugins ({len(installed)}):[/bold]\n")

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Plugin", style="cyan", min_width=20)
    table.add_column("Version", min_width=10)
    table.add_column("Directory", style="dim")
    table.add_column("Source", style="dim")

    for plugin in installed:
        table.add_row(
            plugin["slug"],
            plugin["version"],
            plugin["dir_name"],
            plugin["source"],
        )

    console.print(table)
    console.print()
