"""gdpm create command."""

from __future__ import annotations

import subprocess
from pathlib import Path

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.godot import _get_engines_dir, _normalize_version
from gdpm.config.local_engines import get_default_engine, get_local_engine
from gdpm.config.project import ProjectConfig, write_project_config


def _get_latest_version() -> str:
    """Get the latest installed Godot version."""
    engines_dir = _get_engines_dir()

    versions = []
    if engines_dir.exists():
        for d in engines_dir.iterdir():
            if d.is_dir() and d.name[0].isdigit():
                versions.append(d.name)

    # Also check local engines
    default = get_default_engine()
    if default:
        _, ver = default.split("@", 1)
        versions.append(ver)

    if not versions:
        return ""

    # Sort and return latest stable
    stable = [v for v in versions if "stable" in v]
    if stable:
        return sorted(stable)[-1]
    return sorted(versions)[-1]


def _get_godot_version_tag(version: str) -> str:
    """Convert version to features tag.

    '4.7-stable' -> '4.7'
    '3.6.2-stable' -> '3.6'
    """
    ver = version.replace("-stable", "").replace("-rc", "").replace("-beta", "")
    parts = ver.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return ver


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm create", "Interactive create"),
        ("gdpm create my-game", "Create with name"),
        ("gdpm create my-game --open", "Create and open Godot"),
    ],
)
@click.argument("name", required=False)
@click.option(
    "--open", "-o", "open_editor", is_flag=True,
    help="Open Godot after create",
)
@click.option("--yes", "-y", is_flag=True, help="Use defaults, skip prompts")
def create(name: str | None, open_editor: bool, yes: bool) -> None:
    """Create a new Godot project."""
    project_dir = Path.cwd()

    # Get project name
    if not name:
        if yes:
            name = "gdpm-project"
        else:
            name = click.prompt("  Project name", default="gdpm-project", type=str)

    # Check if directory already exists
    target_dir = project_dir / name if name != project_dir.name else project_dir
    config_path = target_dir / "gdproject.toml"

    if config_path.exists():
        console.print(
            f"[red]Error:[/red] Project already exists "
            f"([cyan]{config_path}[/cyan])"
        )
        return

    # Get Godot version
    latest = _get_latest_version()
    default_ver = latest or "4.7"

    if yes:
        godot_ver = default_ver
    else:
        godot_ver = click.prompt("  Godot version", default=default_ver, type=str)

    # Normalize version
    for suffix in ("-stable", "-csharp", "-mono"):
        godot_ver = godot_ver.replace(suffix, "")
    version_tag = _get_godot_version_tag(godot_ver)

    # Create directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Create project.godot
    project_godot = target_dir / "project.godot"

    major = int(version_tag.split(".")[0])
    if major >= 4:
        project_godot.write_text(
            f"""; Engine configuration file.
; It's best edited using the editor UI and not directly.

config_version=5

[application]

config/name="{name}"
config/features=PackedStringArray("{version_tag}")
""",
            encoding="utf-8",
        )
    else:
        project_godot.write_text(
            f"""; Engine configuration file.
; It's best edited using the editor UI and not directly.

config_version=4

[application]

config/name="{name}"
config/version="{version_tag}.0"
""",
            encoding="utf-8",
        )

    # Create addons/
    addons_dir = target_dir / "addons"
    addons_dir.mkdir(exist_ok=True)

    # Generate gdproject.toml
    config = ProjectConfig(
        name=name,
        godot=f">={version_tag}.0",
    )
    write_project_config(config, config_path)

    console.print(
        f"[green]✓[/green] Created project [bold]{name}[/bold]\n"
        f"  Godot: [cyan]>={version_tag}.0[/cyan]\n"
        "  Created [cyan]project.godot[/cyan]\n"
        "  Created [cyan]gdproject.toml[/cyan]\n"
        "  Created [cyan]addons/[/cyan]"
    )

    # Open Godot
    if open_editor:
        _open_godot(target_dir, godot_ver)


def _open_godot(project_dir: Path, version: str) -> None:
    """Open Godot editor for the project."""
    binary = ""

    # Check default engine
    default = get_default_engine()
    if default:
        name, ver = default.split("@", 1)
        if name == "gdpm-godot":
            engines_dir = _get_engines_dir()
            tag = _normalize_version(ver)
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

    if not binary:
        console.print("[dim]  Skipping open: no Godot engine configured[/dim]")
        return

    try:
        subprocess.Popen(
            [binary, "-e", "--path", str(project_dir)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        console.print("  Opening [cyan]Godot[/cyan]...")
    except Exception as e:
        console.print(f"  [yellow]Warning:[/yellow] Failed to open Godot: {e}")
