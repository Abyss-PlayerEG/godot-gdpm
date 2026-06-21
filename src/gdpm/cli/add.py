"""gdpm add command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from gdpm.cache.file_cache import FileCache
from gdpm.cli.common import is_template, require_project
from gdpm.config.project import read_project_config, write_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile, write_lockfile
from gdpm.models.dependency import Dependency
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient
from gdpm.utils.version import is_compatible

console = Console()


@click.command()
@click.argument("plugins", nargs=-1, required=True)
@click.option("--dev", is_flag=True, help="Add as dev dependency")
def add(plugins: tuple[str, ...], dev: bool) -> None:
    """Add one or more plugins to the project."""

    async def _add() -> None:
        root = require_project()
        config_path = root / "gdproject.toml"
        config = read_project_config(config_path)
        addons_dir = root / config.addons_dir

        store = StoreClient()
        cache_dir = root / ".gdpm" / "cache"
        cache = FileCache(cache_dir)
        manager = PluginManager(addons_dir, cache, store)

        results: list[dict[str, str]] = []
        errors: list[str] = []

        try:
            for plugin_spec in plugins:
                name, version_constraint = _parse_spec(plugin_spec)

                parts = name.split("/")
                if len(parts) == 2:
                    publisher, slug = parts
                else:
                    publisher = ""
                    slug = name

                if slug in config.dependencies or slug in config.dev_dependencies:
                    console.print(
                        f"[yellow]![/yellow] [bold]{slug}[/bold] "
                        "already in dependencies. Use 'gdpm update' to update."
                    )
                    continue

                if not publisher:
                    search_results = await store.search(slug, limit=20)
                    if not search_results:
                        errors.append(f"Plugin '{slug}' not found in Godot Store")
                        continue

                    exact = next((r for r in search_results if r.slug == slug), None)
                    if exact:
                        publisher = exact.publisher_slug
                    else:
                        errors.append(
                            f"Plugin '{slug}' not found. "
                            f"Did you mean: {search_results[0].slug}?"
                        )
                        continue

                try:
                    detail = await store.get_plugin(publisher, slug)
                    if is_template(detail.tags):
                        errors.append(
                            f"'{slug}' is a project template, not an addon. "
                            "Use 'gdpm download' for templates and resources."
                        )
                        continue
                except Exception:
                    pass

                versions = await store.get_versions(publisher, slug)
                if versions:
                    latest = versions[0]
                    ver = latest.get("version", "")
                    min_godot = latest.get("min_godot_version", "")
                    max_godot = latest.get("max_godot_version", "")

                    ver_display = ver if ver.startswith(("v", "V")) else f"v{ver}"
                    console.print(f"  [dim]{ver_display}[/dim]")

                    godot_parts = []
                    if min_godot and min_godot not in ("None", ""):
                        godot_parts.append(f">={min_godot}")
                    if max_godot and max_godot not in ("None", ""):
                        godot_parts.append(f"<={max_godot}")

                    if godot_parts:
                        console.print(
                            f"  [dim]Godot {' '.join(godot_parts)}[/dim]"
                        )

                    compatible, msg = is_compatible(
                        config.godot, min_godot, max_godot
                    )
                    if compatible:
                        console.print("  [green]✓ Compatible[/green]")
                    else:
                        console.print(f"  [red]✗ {msg}[/red]")

                try:
                    with Progress(
                        TextColumn("[bold blue]{task.fields[name]}"),
                        BarColumn(),
                        DownloadColumn(),
                        TransferSpeedColumn(),
                        TimeRemainingColumn(),
                    ) as progress:
                        task_id = progress.add_task("download", name=slug, total=None)

                        def on_progress(
                            current: int,
                            total: int,
                            speed: float,
                            _task: TaskID = task_id,
                        ) -> None:
                            if progress.tasks[_task].total is None:
                                progress.update(_task, total=total)
                            progress.update(_task, completed=current)

                        zip_path, ver = await manager.download(
                            publisher, slug, on_progress=on_progress
                        )

                    manager.install_from_zip(zip_path, slug, publisher)

                    result = {
                        "name": slug,
                        "version": ver,
                        "source": f"store+{publisher}/{slug}",
                    }
                    results.append(result)
                except Exception as e:
                    if "404" in str(e):
                        search_results = await store.search(slug, limit=5)
                        exact = next(
                            (r for r in search_results if r.slug == slug),
                            None,
                        )
                        if exact:
                            errors.append(
                                f"Plugin '{slug}' not found at '{publisher}'. "
                                f"Did you mean: "
                                f"{exact.publisher_slug}/{slug}?"
                            )
                        else:
                            errors.append(f"Failed to install {slug}: {e}")
                    else:
                        errors.append(f"Failed to install {slug}: {e}")
                    continue

                dep = Dependency.from_spec(
                    slug,
                    version_constraint or result["version"],
                    publisher_slug=publisher,
                    is_dev=dev,
                )

                if dev:
                    config.dev_dependencies[slug] = dep
                else:
                    config.dependencies[slug] = dep

        finally:
            await manager.close()

        if results:
            write_project_config(config, config_path)

            lock_path = find_lockfile(root)
            lock_entries = read_lockfile(lock_path)
            lock_map = {e.name: e for e in lock_entries}

            for r in results:
                lock_map[r["name"]] = LockEntry(
                    name=r["name"],
                    version=r["version"],
                    source=r.get("source", ""),
                )

            write_lockfile(list(lock_map.values()), lock_path)

            for r in results:
                ver = r["version"]
                console.print(f"[green]✓[/green] Added [bold]{r['name']}[/bold] {ver}")

            console.print("  Updated [cyan]gdproject.toml[/cyan]")
            console.print("  Updated [cyan]gdpm.lock[/cyan]")

        if errors:
            for err in errors:
                console.print(f"[red]✗[/red] {err}")

        if not results and errors:
            raise SystemExit(1)

    asyncio.run(_add())


def _parse_spec(spec: str) -> tuple[str, str]:
    if "@" in spec:
        name, constraint = spec.split("@", 1)
        return name, constraint
    return spec, ""
