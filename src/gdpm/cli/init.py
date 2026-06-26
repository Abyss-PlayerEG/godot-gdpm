"""gdpm init command."""

from __future__ import annotations

from pathlib import Path

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.config.project import ProjectConfig, write_project_config
from gdpm.utils.godot import detect_version_constraint, parse_project_godot


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm init", "Initialize with auto-detected settings"),
    ],
)
def init() -> None:
    """Initialize a new gdpm project."""
    project_dir = Path.cwd()
    config_path = project_dir / "gdproject.toml"

    if config_path.exists():
        console.print(
            "[red]Error:[/red] Project is already initialized "
            f"([cyan]{config_path}[/cyan] exists)"
        )
        raise SystemExit(1)

    project_file = project_dir / "project.godot"

    if not project_file.exists():
        console.print(
            "[red]Error:[/red] No [cyan]project.godot[/cyan] found "
            "in current directory.\n"
            "  Run this command in a Godot project directory, "
            "or use [bold]gdpm create[/bold]."
        )
        raise SystemExit(1)

    godot_project = parse_project_godot(project_file)

    if not godot_project.name:
        console.print(
            "[red]Error:[/red] Invalid [cyan]project.godot[/cyan] "
            "- no project name found.\n"
            "  Make sure the file contains "
            "[dim]config/name=\"...\"[/dim]"
        )
        raise SystemExit(1)

    if godot_project.config_version < 4:
        console.print(
            f"[red]Error:[/red] Unsupported Godot version "
            f"(config_version={godot_project.config_version}).\n"
            "  gdpm supports Godot 3.x and 4.x only."
        )
        raise SystemExit(1)

    name = godot_project.name or project_dir.name

    godot = detect_version_constraint(project_dir)
    detected = ""
    if godot_project.godot_version:
        detected = (
            f"  [dim]Detected Godot {godot_project.godot_version} "
            f"from project.godot[/dim]\n"
        )

    config = ProjectConfig(
        name=name,
        godot=godot,
    )

    write_project_config(config, config_path)

    addons_dir = project_dir / config.addons_dir
    addons_dir.mkdir(exist_ok=True)

    console.print(
        f"{detected}"
        f"[green]✓[/green] Initialized [bold]{name}[/bold]\n"
        f"  Godot: [cyan]{godot}[/cyan]\n"
        f"  Created [cyan]gdproject.toml[/cyan]\n"
        f"  Created [cyan]{config.addons_dir}/[/cyan]"
    )
