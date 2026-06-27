"""CLI display utilities."""

from __future__ import annotations

from gdpm.cli.common import console
from gdpm.utils.version import is_compatible


def format_version_info(
    ver: str,
    min_godot: str,
    max_godot: str,
    project_godot: str = "",
) -> list[str]:
    """Format version and compatibility info."""
    lines = []
    ver_display = ver if ver.startswith(("v", "V")) else f"v{ver}"
    lines.append(f"    [dim]{ver_display}[/dim]")

    godot_parts = []
    if min_godot and min_godot not in ("None", ""):
        godot_parts.append(f">={min_godot}")
    if max_godot and max_godot not in ("None", ""):
        godot_parts.append(f"<={max_godot}")

    if godot_parts:
        lines.append(f"    [dim]Godot {' '.join(godot_parts)}[/dim]")

    if project_godot:
        compatible, msg = is_compatible(project_godot, min_godot, max_godot)
        if compatible:
            lines.append("    [green]✓ Compatible[/green]")
        else:
            lines.append(f"    [red]✗ {msg}[/red]")

    return lines


def format_plugin_meta(
    license_name: str = "",
    stars: int = 0,
    tags: list[str] | None = None,
    store_url: str = "",
) -> list[str]:
    """Format plugin metadata lines."""
    lines = []
    parts = []
    if license_name:
        parts.append(f"License: {license_name}")
    if stars:
        parts.append(f"Score: {stars}")
    meta = "  |  ".join(parts)
    if meta:
        lines.append(f"    [dim]{meta}[/dim]")
    if tags:
        lines.append(f"    [dim]Tags: {', '.join(tags)}[/dim]")
    if store_url:
        lines.append(f"    [dim]{store_url}[/dim]")
    return lines


def display_version_info(
    ver: str,
    min_godot: str,
    max_godot: str,
    project_godot: str = "",
) -> None:
    """Display version and compatibility info."""
    lines = format_version_info(ver, min_godot, max_godot, project_godot)
    console.print("\n".join(lines))


def display_plugin_meta(
    license_name: str = "",
    stars: int = 0,
    tags: list[str] | None = None,
    store_url: str = "",
) -> None:
    """Display plugin metadata."""
    lines = format_plugin_meta(license_name, stars, tags, store_url)
    console.print("\n".join(lines))


def output_json(data: object) -> None:
    """Output data as JSON."""
    import json

    console.print(json.dumps(data, indent=2, ensure_ascii=False))
