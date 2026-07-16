"""gdpm godot open command."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, find_project_root
from gdpm.cli.godot.common import get_engines_dir, normalize_version


@click.command(
    name="open",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot open", "Open Godot editor"),
        ("gdpm godot open --run", "Run the project"),
    ],
)
@click.option(
    "--run", "-r", is_flag=True, help="Run the project instead of opening editor"
)
def godot_open(run: bool) -> None:
    """Open Godot editor for the current project."""
    from gdpm.config.local_engines import get_default_engine, get_local_engine

    root = find_project_root()
    conf_path = root / ".engines-conf.json"
    binary = ""

    engine_name = "?"
    engine_ver = "?"

    if conf_path.exists():
        try:
            conf = json.loads(conf_path.read_text(encoding="utf-8"))
            godot = conf.get("godot", {})
            binary = godot.get("path", "")
            engine_name = godot.get("name", "?")
            engine_ver = godot.get("version", "?")
        except json.JSONDecodeError, TypeError:
            pass

    if not binary:
        default_id = get_default_engine()
        if default_id:
            name, version = default_id.split("@", 1)
            if name == "gdpm-godot":
                engines_dir = get_engines_dir()
                tag = normalize_version(version)
                ver_dir = engines_dir / tag
                if ver_dir.exists():
                    for app in ver_dir.glob("*.app"):
                        b = app / "Contents" / "MacOS" / "Godot"
                        if b.exists():
                            binary = str(b)
                            break
                    if not binary:
                        for f in ver_dir.iterdir():
                            if f.is_file() and not f.suffix:
                                binary = str(f)
                                break
            else:
                engine = get_local_engine(name)
                if engine:
                    binary = engine.path

            engine_name = name
            engine_ver = version

    if not binary:
        console.print(
            "[red]Error:[/red] No Godot engine configured.\n"
            "  Use [bold]gdpm godot use <id>[/bold] for this project,\n"
            "  or [bold]gdpm godot default <id>[/bold] to set a default engine.\n"
            "\n"
            "  Available engines:\n"
            "    [bold]gdpm godot list -id[/bold]"
        )
        return

    binary_path = Path(binary)
    if binary_path.suffix == ".app":
        macos_binary = binary_path / "Contents" / "MacOS" / "Godot"
        if macos_binary.exists():
            binary = str(macos_binary)

    args = [binary]
    if run:
        args.extend(["--path", str(root)])
    else:
        args.extend(["-e", "--path", str(root)])

    console.print(f"Opening [cyan]{engine_name}@{engine_ver}[/cyan]...")

    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ret = proc.poll()
        if ret is not None and ret != 0:
            console.print(f"[red]Error:[/red] Godot exited with code {ret}")
            return
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to open Godot: {e}")
        return

    console.print(f"[green]✓[/green] Opened [cyan]{engine_name}@{engine_ver}[/cyan]")
