"""gdpm create command."""

from __future__ import annotations

import subprocess
from pathlib import Path

import click
import questionary

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.godot import _get_engines_dir, _normalize_version
from gdpm.config.local_engines import get_default_engine, get_local_engine
from gdpm.config.project import ProjectConfig, write_project_config


def _get_installed_engines() -> list[str]:
    """Get all installed engine IDs.

    Returns list of IDs like ['gdpm-godot@4.7-stable', 'steam@4.7-stable']
    """
    engines: list[str] = []

    # Downloaded engines
    engines_dir = _get_engines_dir()
    if engines_dir.exists():
        for d in engines_dir.iterdir():
            is_engine = d.is_dir() and d.name[0].isdigit()
            is_standard = "-csharp" not in d.name and "-mono" not in d.name
            if is_engine and is_standard:
                engines.append(f"gdpm-godot@{d.name}")

    # Local engines
    from gdpm.config.local_engines import load_local_engines

    for name, engine in load_local_engines().items():
        if engine.version:
            engines.append(f"{name}@{engine.version}")

    # Sort: stable first, then by version descending
    def sort_key(item: str) -> tuple[int, str]:
        ver = item.split("@", 1)[1]
        is_stable = 0 if "stable" in ver else 1
        return (is_stable, ver)

    engines.sort(key=sort_key, reverse=True)
    return engines


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

    console.print("[bold cyan]✦ Create a new Godot project[/bold cyan]")

    # Get project name
    if not name:
        if yes:
            name = "gdpm-project"
        else:
            name = questionary.text(
                "Project name:",
                default="gdpm-project",
            ).ask()
            if not name:
                return

    # Check if directory already exists
    target_dir = project_dir / name if name != project_dir.name else project_dir
    config_path = target_dir / "gdproject.toml"

    if config_path.exists():
        console.print(
            f"  [red]✖[/red] Project already exists "
            f"([cyan]{config_path}[/cyan])"
        )
        return

    # Get Godot version
    engines = _get_installed_engines()
    versions = [e.split("@", 1)[1] for e in engines]
    # Deduplicate
    seen: set[str] = set()
    unique_versions: list[str] = []
    for v in versions:
        if v not in seen:
            seen.add(v)
            unique_versions.append(v)

    default_ver = unique_versions[0] if unique_versions else "4.7-stable"

    if yes:
        godot_ver = default_ver
    elif unique_versions:
        godot_ver = questionary.select(
            "Godot version:",
            choices=unique_versions,
            default=default_ver,
        ).ask()
        if not godot_ver:
            return
    else:
        godot_ver = questionary.text(
            "Godot version:",
            default="4.7-stable",
        ).ask()
        if not godot_ver:
            return

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

    # Show success
    console.print(
        f"\n  [green]✔[/green] Project [bold]{name}[/bold] created successfully!\n"
        f"  [dim]Godot:[/dim]     [cyan]>={version_tag}.0[/cyan]\n"
        f"  [dim]Directory:[/dim] [cyan]{target_dir}[/cyan]\n"
        f"  [dim]Files created:[/dim]\n"
        f"    [cyan]project.godot[/cyan]\n"
        f"    [cyan]gdproject.toml[/cyan]\n"
        f"    [cyan]addons/[/cyan]"
    )

    # Optional: set engine for this project
    engines = _get_installed_engines()
    if engines and not yes:
        set_engine = questionary.confirm(
            "Set Godot engine for this project?",
            default=True,
        ).ask()

        if set_engine:
            engine_id = ""
            if len(engines) == 1:
                engine_id = engines[0]
            else:
                engine_id = questionary.select(
                    "Select engine:",
                    choices=engines,
                    default=engines[0],
                ).ask()

            if engine_id:
                _set_project_engine(target_dir, engine_id)

    # Open Godot
    if open_editor:
        _open_godot(target_dir, godot_ver)


def _set_project_engine(project_dir: Path, engine_id: str) -> None:
    """Set the Godot engine for a project."""
    import json

    from gdpm.cli.godot import _get_engines_dir, _normalize_version

    name, version = engine_id.split("@", 1)

    # Find engine binary
    binary = ""
    if name == "gdpm-godot":
        engines_dir = _get_engines_dir()
        tag = _normalize_version(version)
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
        from gdpm.config.local_engines import get_local_engine

        engine = get_local_engine(name)
        if engine:
            binary = engine.path

    if not binary:
        console.print("  [dim]Skipping engine setup: engine not found[/dim]")
        return

    # Write .engines-conf.json
    conf_path = project_dir / ".engines-conf.json"
    conf = {"godot": {"name": name, "version": version, "path": binary}}
    conf_path.write_text(
        json.dumps(conf, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    console.print(f"  [dim]Engine:[/dim] [cyan]{name}@{version}[/cyan]")


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
