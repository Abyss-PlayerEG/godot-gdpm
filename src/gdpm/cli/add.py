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
from gdpm.cli.options import yes_option
from gdpm.config.project import read_project_config, write_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile, write_lockfile
from gdpm.models.dependency import Dependency
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient
from gdpm.utils.version import is_compatible

console = Console()


@click.command()
@click.argument("plugins", nargs=-1)
@click.option("--dev", is_flag=True, help="Add as dev dependency")
@click.option("--local", is_flag=True, help="Pack local plugins to gdpm-local/")
@yes_option
def add(plugins: tuple[str, ...], dev: bool, local: bool, yes: bool) -> None:
    """Add one or more plugins to the project."""
    if local:
        _add_local(plugins, yes=yes)
        return

    if not plugins:
        console.print("[red]Error:[/red] No plugins specified.")
        raise SystemExit(1)

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
                        console.print(f"  [dim]Godot {' '.join(godot_parts)}[/dim]")

                    compatible, msg = is_compatible(config.godot, min_godot, max_godot)
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


def _add_local(plugins: tuple[str, ...], yes: bool = False) -> None:
    """Pack local plugins to gdpm-local/ with hash comparison."""
    from gdpm.utils.local import (
        LOCAL_DIR_NAME,
        compute_dir_hash,
        find_matching_hash,
        load_hashes,
        pack_plugin,
        save_hashes,
        scan_untagged_or_local_plugins,
        tag_plugin,
    )

    root = require_project()
    config_path = root / "gdproject.toml"
    config = read_project_config(config_path)
    addons_dir = root / config.addons_dir
    local_dir = root / LOCAL_DIR_NAME

    if plugins:
        targets = list(plugins)
    else:
        untagged = scan_untagged_or_local_plugins(addons_dir)
        if not untagged:
            console.print("[dim]No local plugins found in addons/[/dim]")
            return
        targets = [p.name for p in untagged]

    if not targets:
        console.print("[dim]No plugins to pack.[/dim]")
        return

    hashes = load_hashes(root)
    console.print(f"Scanning {len(targets)} plugin(s)...\n")

    packed = 0
    skipped = 0
    renamed = 0

    for name in targets:
        plugin_dir = addons_dir / name
        if not plugin_dir.exists():
            console.print(f"[red]✗[/red] Plugin directory not found: {name}")
            continue

        content_hash = compute_dir_hash(plugin_dir)

        # Check if hash matches an existing plugin (possible rename)
        existing_name = find_matching_hash(hashes, content_hash)

        if existing_name and existing_name != name:
            # Rename detected
            old_zip = local_dir / f"{existing_name}.zip"
            new_zip = local_dir / f"{name}.zip"

            if (
                old_zip.exists()
                and not yes
                and not console.input(
                    f"  [yellow]?[/yellow] {name} matches "
                    f"[bold]{existing_name}[/bold]. Rename? (y/n): "
                )
                .strip()
                .lower()
                .startswith("y")
            ):
                # User declined rename, treat as new plugin
                existing_name = None

            if existing_name and existing_name != name:
                if old_zip.exists():
                    old_zip.rename(new_zip)
                hashes.pop(existing_name, None)
                hashes[name] = content_hash
                tag_plugin(addons_dir, name)

                # Update dependency name
                if existing_name in config.dependencies:
                    dep = config.dependencies.pop(existing_name)
                    config.dependencies[name] = dep

                console.print(
                    f"[green]✓[/green] Renamed [bold]{existing_name}[/bold] "
                    f"→ [bold]{name}[/bold]"
                )
                renamed += 1
                continue

        # Check if content changed
        zip_exists = (local_dir / f"{name}.zip").exists()
        is_registered = name in config.dependencies or name in config.dev_dependencies

        if not zip_exists or not is_registered:
            # Zip was deleted or not registered, force repack
            pass
        elif name in hashes and hashes[name] == content_hash:
            console.print(f"  [dim]○ {name}: unchanged → skipped[/dim]")
            skipped += 1
            continue

        # Pack the plugin
        tag_plugin(addons_dir, name)
        pack_plugin(addons_dir, name, local_dir)
        hashes[name] = content_hash

        dep = Dependency.from_spec(name, "*", is_local=True, is_dev=False)
        config.dependencies[name] = dep

        console.print(
            f"[green]✓[/green] Packed [bold]{name}[/bold] → {LOCAL_DIR_NAME}/{name}.zip"
        )
        packed += 1

    if packed or renamed:
        save_hashes(root, hashes)
        write_project_config(config, config_path)

        # Update lock file
        lock_path = find_lockfile(root)
        lock_entries = read_lockfile(lock_path)
        lock_map = {e.name: e for e in lock_entries}

        for name in targets:
            plugin_dir = addons_dir / name
            if plugin_dir.exists():
                lock_map[name] = LockEntry(
                    name=name,
                    version="local",
                    source="local",
                )

        write_lockfile(list(lock_map.values()), lock_path)

        console.print()
        if packed:
            console.print(f"  Packed: {packed}")
        if renamed:
            console.print(f"  Renamed: {renamed}")
        if skipped:
            console.print(f"  Skipped: {skipped}")
        console.print("  Updated [cyan]gdproject.toml[/cyan]")
        console.print("  Updated [cyan]gdpm.lock[/cyan]")
        console.print(f"  Updated [cyan]{LOCAL_DIR_NAME}/.hashes[/cyan]")
