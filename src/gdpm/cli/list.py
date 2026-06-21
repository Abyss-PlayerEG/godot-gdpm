"""gdpm list command."""

from __future__ import annotations

import configparser

import click
from rich.console import Console

from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile

console = Console()


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

    installed: list[dict[str, str]] = []

    if addons_dir.exists():
        for child in sorted(addons_dir.iterdir()):
            if not child.is_dir():
                continue

            cfg_path = child / "plugin.cfg"
            name = child.name
            version = "?"

            if cfg_path.exists():
                try:
                    parser = configparser.ConfigParser()
                    parser.read(cfg_path)
                    name = parser.get("plugin", "name", fallback=child.name)
                    version = parser.get("plugin", "version", fallback="?")
                except Exception:
                    pass

            locked = lock_map.get(child.name)
            if locked:
                version = locked.version

            installed.append(
                {
                    "name": child.name,
                    "display_name": name,
                    "version": version,
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

    for plugin in installed:
        console.print(f"  [cyan]{plugin['name']}[/cyan]  v{plugin['version']}")

    console.print()
