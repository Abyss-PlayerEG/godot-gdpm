"""gdpm remove command."""

from __future__ import annotations

import configparser
from typing import TYPE_CHECKING

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, require_project
from gdpm.cli.options import yes_option
from gdpm.config.project import read_project_config, write_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile, write_lockfile

if TYPE_CHECKING:
    from pathlib import Path


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm remove limbo-ai", "Remove a plugin"),
        ("gdpm remove -y limbo-ai", "Remove without confirmation"),
        ("gdpm remove -r limbo-ai", "Remove with sub-dependencies"),
    ],
)
@click.argument("plugins", nargs=-1, required=True)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Also remove unused sub-dependencies",
)
@yes_option
def remove(plugins: tuple[str, ...], recursive: bool, yes: bool) -> None:
    """Remove one or more plugins from the project."""
    root = require_project()
    config_path = root / "gdproject.toml"
    config = read_project_config(config_path)
    addons_dir = root / config.addons_dir
    local_dir = root / "gdpm-local"

    removed: list[str] = []
    not_found: list[str] = []

    for name in plugins:
        slug = name.split("/")[-1]

        if slug not in config.dependencies and slug not in config.dev_dependencies:
            not_found.append(slug)
            continue

        # Check if local plugin
        dep = config.dependencies.get(slug) or config.dev_dependencies.get(slug)
        is_local = dep.is_local if dep else False

        config.dependencies.pop(slug, None)
        config.dev_dependencies.pop(slug, None)

        # Remove addon directory
        actual_dir = _find_addon_dir(addons_dir, slug)
        if actual_dir and actual_dir.exists():
            import shutil

            shutil.rmtree(actual_dir)

        # Remove local zip if exists
        if is_local:
            local_zip = local_dir / f"{slug}.zip"
            if local_zip.exists():
                delete_zip = yes or click.confirm(
                    f"  Delete {local_dir.name}/{slug}.zip?"
                )
                if delete_zip:
                    local_zip.unlink()
                    console.print(f"  [dim]Removed {local_dir.name}/{slug}.zip[/dim]")

        removed.append(slug)

    if removed:
        write_project_config(config, config_path)

        lock_path = find_lockfile(root)
        lock_entries = read_lockfile(lock_path)
        lock_map = {e.name: e for e in lock_entries}

        for name in plugins:
            slug = name.split("/")[-1]
            lock_map.pop(slug, None)

        write_lockfile(list(lock_map.values()), lock_path)

        for name in removed:
            console.print(f"[green]✓[/green] Removed [bold]{name}[/bold]")
        console.print("  Updated [cyan]gdproject.toml[/cyan]")
        console.print("  Updated [cyan]gdpm.lock[/cyan]")

    if not_found:
        for name in not_found:
            console.print(
                f"[yellow]![/yellow] Plugin [bold]{name}[/bold] "
                "not found in dependencies"
            )

    if not removed and not_found:
        raise SystemExit(1)


def _find_addon_dir(addons_dir: Path, slug: str) -> Path | None:
    if not addons_dir.exists():
        return None

    direct = addons_dir / slug
    if direct.exists():
        return direct

    for child in addons_dir.iterdir():
        if not child.is_dir():
            continue
        cfg = child / "plugin.cfg"
        if cfg.exists():
            try:
                parser = configparser.ConfigParser()
                parser.read(cfg)
                plugin_name = parser.get("plugin", "name", fallback="")
                if slug.replace("-", " ").lower() in plugin_name.lower():
                    return child
                if slug.replace("-", "_") == child.name:
                    return child
            except Exception:
                continue

    return None
