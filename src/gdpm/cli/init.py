"""gdpm init command."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from gdpm.config.project import ProjectConfig, write_project_config

console = Console()


@click.command()
@click.argument("name", required=False)
@click.option("--godot", default=">=4.0", help="Godot version constraint")
@click.option("--license", "license_id", default="MIT", help="SPDX license ID")
@click.option("--as-plugin", is_flag=True, help="Initialize as a plugin project")
@click.option("--force", is_flag=True, help="Overwrite existing gdproject.toml")
def init(
    name: str | None,
    godot: str,
    license_id: str,
    as_plugin: bool,
    force: bool,
) -> None:
    """Initialize a new gdpm project."""
    project_dir = Path.cwd()
    config_path = project_dir / "gdproject.toml"

    if config_path.exists() and not force:
        console.print(
            "[red]Error:[/red] gdproject.toml already exists. Use --force to overwrite."
        )
        raise SystemExit(1)

    if name is None:
        name = project_dir.name

    config = ProjectConfig(
        name=name,
        godot=godot,
        license=license_id,
    )

    write_project_config(config, config_path)

    addons_dir = project_dir / config.addons_dir
    addons_dir.mkdir(exist_ok=True)

    console.print(f"[green]✓[/green] Initialized [bold]{name}[/bold]")
    console.print("  Created [cyan]gdproject.toml[/cyan]")
    console.print(f"  Created [cyan]{config.addons_dir}/[/cyan]")
