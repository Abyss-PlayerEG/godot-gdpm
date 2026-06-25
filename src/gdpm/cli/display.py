"""CLI display utilities."""

from __future__ import annotations

from gdpm.cli.common import console
from gdpm.utils.version import is_compatible


def display_version_info(
    ver: str,
    min_godot: str,
    max_godot: str,
    project_godot: str = "",
) -> None:
    """Display version and compatibility info."""
    ver_display = ver if ver.startswith(("v", "V")) else f"v{ver}"
    console.print(f"    [dim]{ver_display}[/dim]")

    godot_parts = []
    if min_godot and min_godot not in ("None", ""):
        godot_parts.append(f">={min_godot}")
    if max_godot and max_godot not in ("None", ""):
        godot_parts.append(f"<={max_godot}")

    if godot_parts:
        console.print(f"    [dim]Godot {' '.join(godot_parts)}[/dim]")

    if project_godot:
        compatible, msg = is_compatible(project_godot, min_godot, max_godot)
        if compatible:
            console.print("    [green]✓ Compatible[/green]")
        else:
            console.print(f"    [red]✗ {msg}[/red]")


def display_plugin_meta(
    license_name: str = "",
    stars: int = 0,
    tags: list[str] | None = None,
    store_url: str = "",
) -> None:
    """Display plugin metadata line."""
    parts = []
    if license_name:
        parts.append(f"License: {license_name}")
    if stars:
        parts.append(f"Score: {stars}")
    meta = "  |  ".join(parts)
    if meta:
        console.print(f"    [dim]{meta}[/dim]")
    if tags:
        console.print(f"    [dim]Tags: {', '.join(tags)}[/dim]")
    if store_url:
        console.print(f"    [dim]{store_url}[/dim]")


def output_json(data: object) -> None:
    """Output data as JSON."""
    import json

    console.print(json.dumps(data, indent=2, ensure_ascii=False))
