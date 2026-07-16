"""gdpm godot info command."""

from __future__ import annotations

import json

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, find_project_root
from gdpm.cli.godot.common import get_engines_dir, normalize_version


@click.command(
    name="info",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot info", "Show current Godot engine info"),
    ],
)
def godot_info() -> None:
    """Show current Godot engine configuration."""
    from gdpm.config.local_engines import get_default_engine, get_local_engine
    from gdpm.utils.path import shorten_path

    root = find_project_root()
    conf_path = root / ".engines-conf.json"

    name = ""
    version = ""
    path = ""

    is_default = False
    if conf_path.exists():
        try:
            conf = json.loads(conf_path.read_text(encoding="utf-8"))
            godot = conf.get("godot", {})
            if godot:
                name = godot.get("name", "")
                version = godot.get("version", "")
                path = godot.get("path", "")
        except json.JSONDecodeError, TypeError:
            pass

    if not name:
        is_default = True
        default_id = get_default_engine()
        if default_id:
            default_name, default_ver = default_id.split("@", 1)
            name = default_name
            version = default_ver

            if default_name == "gdpm-godot":
                engines_dir = get_engines_dir()
                tag = normalize_version(default_ver)
                ver_dir = engines_dir / tag
                if ver_dir.exists():
                    for app in ver_dir.glob("*.app"):
                        b = app / "Contents" / "MacOS" / "Godot"
                        if b.exists():
                            path = str(b)
                            break
                    if not path:
                        for f in ver_dir.iterdir():
                            if f.is_file() and not f.suffix:
                                path = str(f)
                                break
            else:
                engine = get_local_engine(default_name)
                if engine:
                    path = engine.path

    if not name:
        console.print(
            "[red]Error:[/red] No Godot engine configured.\n"
            "  Use [bold]gdpm godot use <id>[/bold] for this project,\n"
            "  or [bold]gdpm godot default <id>[/bold] to set a default engine.\n"
            "\n"
            "  Available engines:\n"
            "    [bold]gdpm godot list -id[/bold]"
        )
        return

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )
    table.add_column("Key", style="dim", min_width=12)
    table.add_column("Value", style="cyan")

    table.add_row("Name", f"{name} [dim](default)[/dim]" if is_default else name)
    table.add_row("Version", version)
    table.add_row("Path", shorten_path(path, max_len=50) if path else "-")
    table.add_row("ID", f"{name}@{version}")

    console.print(
        Panel(
            table,
            title="[bold cyan]Godot Engine[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )
