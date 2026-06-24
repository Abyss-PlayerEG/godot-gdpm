"""gdpm init command."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from gdpm.cli.app import GdpmCommand
from gdpm.config.project import ProjectConfig, write_project_config
from gdpm.utils.godot import detect_version_constraint, parse_project_godot

console = Console()


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm init", "Initialize with auto-detected settings"),
        ("gdpm init my-game", "Initialize with custom name"),
        ("gdpm init --godot '>=4.3'", "Specify Godot version"),
    ],
)
@click.argument("name", required=False)
@click.option("--godot", default="", help="Godot version constraint")
def init(
    name: str | None,
    godot: str,
) -> None:
    """Initialize a new gdpm project."""
    project_dir = Path.cwd()
    config_path = project_dir / "gdproject.toml"

    project_file = project_dir / "project.godot"
    godot_project = parse_project_godot(project_file)

    if name is None:
        name = godot_project.name or project_dir.name

    if not godot:
        godot = detect_version_constraint(project_dir)
        if godot_project.godot_version:
            console.print(
                f"  [dim]Detected Godot {godot_project.godot_version} "
                f"from project.godot[/dim]"
            )

    config = ProjectConfig(
        name=name,
        godot=godot,
    )

    write_project_config(config, config_path)

    addons_dir = project_dir / config.addons_dir
    addons_dir.mkdir(exist_ok=True)

    console.print(f"[green]✓[/green] Initialized [bold]{name}[/bold]")
    console.print(f"  Godot: [cyan]{godot}[/cyan]")
    console.print("  Created [cyan]gdproject.toml[/cyan]")
    console.print(f"  Created [cyan]{config.addons_dir}/[/cyan]")
