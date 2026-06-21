"""gdpm update command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console

from gdpm.cache.file_cache import FileCache
from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile, write_lockfile
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient

console = Console()


@click.command()
@click.argument("plugins", nargs=-1)
@click.option("--latest", is_flag=True, help="Ignore version constraints")
@click.option("--dry-run", is_flag=True, help="Preview updates without applying")
def update(plugins: tuple[str, ...], latest: bool, dry_run: bool) -> None:
    """Update plugins to newer versions."""

    async def _update() -> None:
        root = require_project()
        config_path = root / "gdproject.toml"
        config = read_project_config(config_path)
        addons_dir = root / config.addons_dir
        lock_path = find_lockfile(root)

        lock_entries = read_lockfile(lock_path)
        lock_map = {e.name: e for e in lock_entries}

        all_deps = {**config.dependencies, **config.dev_dependencies}

        if plugins:
            targets = {p.split("/")[-1] for p in plugins}
        else:
            targets = set(all_deps.keys())

        store = StoreClient()
        cache_dir = root / ".gdpm" / "cache"
        cache = FileCache(cache_dir)
        manager = PluginManager(addons_dir, cache, store)

        updates: list[dict[str, str]] = []
        errors: list[str] = []
        up_to_date: list[str] = []

        try:
            console.print("Checking for updates...")

            for name in targets:
                dep = all_deps.get(name)
                if not dep:
                    errors.append(f"Plugin '{name}' not in dependencies")
                    continue

                if dep.publisher_slug:
                    publisher = dep.publisher_slug
                else:
                    search_results = await store.search(name, limit=5)
                    exact = next((r for r in search_results if r.slug == name), None)
                    if not exact:
                        errors.append(f"Plugin '{name}' not found")
                        continue
                    publisher = exact.publisher_slug

                try:
                    versions = await store.get_versions(publisher, name)
                except Exception as e:
                    errors.append(f"Failed to fetch versions for '{name}': {e}")
                    continue

                if not versions:
                    errors.append(f"No versions found for '{name}'")
                    continue

                current = lock_map.get(name)
                current_ver = current.version.lstrip("v") if current else ""

                latest_ver = None
                for v in versions:
                    api_ver = v["version"].lstrip("v")
                    if latest or dep.constraint.matches(
                        __import__("gdpm.models.version", fromlist=["Version"]).Version(
                            api_ver
                        )
                    ):
                        latest_ver = v
                        break

                if not latest_ver:
                    errors.append(f"No compatible version for '{name}'")
                    continue

                new_ver = latest_ver["version"]
                if current_ver and new_ver.lstrip("v") == current_ver:
                    up_to_date.append(name)
                    continue

                updates.append(
                    {
                        "name": name,
                        "publisher": publisher,
                        "old_version": current_ver or "none",
                        "new_version": new_ver,
                    }
                )

        finally:
            await manager.close()

        if not updates:
            console.print("[green]✓[/green] All plugins are up to date.")
            return

        console.print(f"\n{len(updates)} update(s) available:\n")
        for u in updates:
            console.print(
                f"  [cyan]{u['name']}[/cyan]  "
                f"{u['old_version']} → [green]{u['new_version']}[/green]"
            )

        if dry_run:
            console.print("\n[yellow]Dry run complete.[/yellow]")
            return

        console.print()

        async def _apply() -> None:
            store2 = StoreClient()
            cache2 = FileCache(cache_dir)
            manager2 = PluginManager(addons_dir, cache2, store2)
            applied = 0

            try:
                for u in updates:
                    try:
                        zip_path, _ver = await manager2.download(
                            u["publisher"],
                            u["name"],
                            u["new_version"].lstrip("v"),
                        )
                        manager2.install_from_zip(zip_path, u["name"], u["publisher"])
                        lock_map[u["name"]] = LockEntry(
                            name=u["name"],
                            version=u["new_version"],
                            source=f"store+{u['publisher']}/{u['name']}",
                        )
                        applied += 1
                        console.print(
                            f"[green]✓[/green] Updated [bold]{u['name']}[/bold] "
                            f"{u['new_version']}"
                        )
                    except Exception as e:
                        console.print(f"[red]✗[/red] Failed to update {u['name']}: {e}")
            finally:
                await manager2.close()

            if applied:
                write_lockfile(list(lock_map.values()), lock_path)
                console.print(f"\n[green]✓[/green] Updated {applied} plugin(s)")

        await _apply()

    asyncio.run(_update())
