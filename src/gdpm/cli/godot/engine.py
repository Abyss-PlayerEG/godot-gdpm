"""gdpm godot engine management commands (add/remove/use/default)."""

from __future__ import annotations

import json
from pathlib import Path

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, find_project_root
from gdpm.cli.godot.common import find_engine


@click.command(
    name="add",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot add /Applications/Godot.app", "Add macOS Godot"),
        ("gdpm godot add /usr/local/bin/godot", "Add Linux Godot"),
        ("gdpm godot add /path/to/Godot --name 4.7-custom", "Add with alias"),
    ],
)
@click.argument("path")
@click.option("--name", "-n", default="", help="Alias for the engine")
def godot_add(path: str, name: str) -> None:
    """Add a local Godot engine."""
    from gdpm.config.local_engines import add_local_engine, load_local_engines
    from gdpm.utils.godot import detect_godot_binary, get_godot_version

    engine_path = Path(path).expanduser().resolve()

    if not engine_path.exists():
        console.print(f"[red]Error:[/red] Path [cyan]{path}[/cyan] does not exist.")
        return

    binary = detect_godot_binary(engine_path)
    if not binary:
        console.print(
            "[red]Error:[/red] Not a valid Godot application.\n"
            "  macOS: provide path to .app bundle\n"
            "  Linux: provide path to executable"
        )
        return

    console.print(
        f"  [dim]✓ Path exists: {engine_path}[/dim]\n"
        f"  [dim]✓ Binary found: {binary.name}[/dim]"
    )

    version = get_godot_version(binary)
    if version:
        console.print(f"  [dim]✓ Version: {version}[/dim]")
    else:
        console.print("  [dim]⚠ Could not detect version[/dim]")

    engines = load_local_engines()
    for existing_name, engine in engines.items():
        if engine.path == str(engine_path):
            console.print(
                f"[yellow]This path is already added as '{existing_name}'.[/yellow]"
            )
            return

    if not name:
        default_name = version or engine_path.stem
        name = click.prompt("  Alias", default=default_name, type=str)

    if name in engines and not click.confirm(
        f"  [yellow]'{name}' already exists. Overwrite?[/yellow]"
    ):
        return

    add_local_engine(name, str(binary), version)
    console.print(f"[green]✓[/green] Added Godot [bold]{name}[/bold]")


@click.command(
    name="remove",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot remove steam-godot", "Remove by name"),
        ("gdpm godot remove steam-godot@4.7-stable", "Remove by ID"),
    ],
)
@click.argument("name_or_id")
def godot_remove(name_or_id: str) -> None:
    """Remove a local Godot engine."""
    from gdpm.config.local_engines import (
        get_default_engine,
        load_local_engines,
        remove_local_engine,
        set_default_engine,
    )

    name = name_or_id.split("@")[0] if "@" in name_or_id else name_or_id

    engines = load_local_engines()
    if name not in engines:
        console.print(
            f"[red]Error:[/red] Local engine [cyan]{name}[/cyan] not found.\n"
            "  Use [bold]gdpm godot list -id[/bold] to see available engines."
        )
        return

    remove_local_engine(name)

    default = get_default_engine()
    if default and default.startswith(f"{name}@"):
        set_default_engine("")

    console.print(f"[green]✓[/green] Removed engine [bold]{name}[/bold]")


@click.command(
    name="use",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot use gdpm-godot@4.7-stable", "Use downloaded engine"),
        ("gdpm godot use steam@4.7-stable", "Use local engine"),
        ("gdpm godot list -id", "List available engine IDs"),
    ],
)
@click.argument("id")
def godot_use(engine_id: str) -> None:
    """Set the Godot engine for the current project."""
    if "@" not in engine_id:
        console.print(
            "[red]Error:[/red] Invalid format. Use [cyan]Name@Version[/cyan]\n"
            "  Example: gdpm godot use gdpm-godot@4.7-stable"
        )
        return

    name, version = engine_id.split("@", 1)

    engine_path = find_engine(name, version)
    if not engine_path:
        console.print(
            f"[red]Error:[/red] Engine [cyan]{engine_id}[/cyan] not found.\n"
            "  Use [bold]gdpm godot list -id[/bold] to see available engines."
        )
        return

    root = find_project_root()
    conf_path = root / ".engines-conf.json"

    conf = {}
    if conf_path.exists():
        try:
            conf = json.loads(conf_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError, TypeError:
            conf = {}

    conf["godot"] = {"name": name, "version": version, "path": engine_path}

    conf_path.write_text(
        json.dumps(conf, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    console.print(f"[green]✓[/green] Set Godot engine to [bold]{name}@{version}[/bold]")


@click.command(
    name="default",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot default", "Show current default engine"),
        ("gdpm godot default steam@4.7-stable", "Set default engine"),
        ("gdpm godot default --unset", "Remove default engine"),
    ],
)
@click.argument("engine_id", required=False)
@click.option("--unset", is_flag=True, help="Remove default engine")
def godot_default(engine_id: str | None, unset: bool) -> None:
    """Set or show the default Godot engine."""
    from gdpm.config.local_engines import (
        get_default_engine,
        load_local_engines,
        set_default_engine,
        unset_default_engine,
    )

    if unset:
        unset_default_engine()
        console.print("[green]✓[/green] Default engine removed")
        return

    if not engine_id:
        default = get_default_engine()
        if default:
            console.print(f"Default engine: [cyan]{default}[/cyan]")
        else:
            console.print(
                "[dim]No default engine configured.[/dim]\n"
                "  Use [bold]gdpm godot default <id>[/bold] to set one.\n"
                "  Use [bold]gdpm godot list -id[/bold] to see available engines."
            )
        return

    if "@" not in engine_id:
        console.print("[red]Error:[/red] Invalid format. Use [cyan]Name@Version[/cyan]")
        return

    name, version = engine_id.split("@", 1)
    engines = load_local_engines()

    if name in engines:
        engine = engines[name]
        if engine.version and engine.version != version:
            console.print(
                f"[red]Error:[/red] Version mismatch. "
                f"Local engine '{name}' is version [cyan]{engine.version}[/cyan]"
            )
            return
    elif name != "gdpm-godot":
        console.print(
            f"[red]Error:[/red] Engine [cyan]{name}[/cyan] not found.\n"
            "  Use [bold]gdpm godot list -id[/bold] to see available engines."
        )
        return

    set_default_engine(engine_id)
    console.print(f"[green]✓[/green] Default engine set to [bold]{engine_id}[/bold]")
