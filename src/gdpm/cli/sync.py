"""gdpm sync command."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import click
from rich.console import Console

from gdpm.cache.file_cache import FileCache
from gdpm.cli.common import require_project
from gdpm.config.project import ProjectConfig, read_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile, write_lockfile
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient

if TYPE_CHECKING:
    from pathlib import Path

console = Console()


@click.command()
@click.option(
    "--frozen",
    is_flag=True,
    help="Strict mode for CI (fail if lock outdated)",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option("--no-cache", is_flag=True, help="Don't use local cache")
def sync(frozen: bool, dry_run: bool, no_cache: bool) -> None:
    """Sync addons/ directory to lock file state."""
    root = require_project()
    config_path = root / "gdproject.toml"
    config = read_project_config(config_path)
    addons_dir = root / config.addons_dir
    lock_path = find_lockfile(root)

    if not lock_path.exists():
        console.print("[yellow]No lock file found. Generating...[/yellow]")
        _generate_lock(root, config, lock_path)

    lock_entries = read_lockfile(lock_path)
    lock_map = {e.name: e for e in lock_entries}
    lock_names = set(lock_map.keys())

    all_deps = {**config.dependencies, **config.dev_dependencies}
    declared_names = set(all_deps.keys())

    # Separate local and online plugins
    local_names = {name for name, dep in all_deps.items() if dep.is_local}
    online_names = declared_names - local_names

    installed_by_dep: set[str] = set()
    if addons_dir.exists():
        for child in addons_dir.iterdir():
            if not child.is_dir():
                continue
            tag_path = child / "tag.gdpm"
            if tag_path.exists():
                tag = tag_path.read_text(encoding="utf-8").strip()
                for name in declared_names:
                    if tag.endswith(f"/{name}"):
                        installed_by_dep.add(name)

    to_install = online_names - installed_by_dep
    to_remove = set()
    if addons_dir.exists():
        for child in addons_dir.iterdir():
            if not child.is_dir():
                continue
            tag_path = child / "tag.gdpm"
            if tag_path.exists():
                tag = tag_path.read_text(encoding="utf-8").strip()
                for name in lock_names:
                    if tag.endswith(f"/{name}") and name not in declared_names:
                        to_remove.add(name)

    if not to_install and not to_remove:
        console.print("[green]✓[/green] Everything is up to date. Nothing to do.")
        return

    if dry_run:
        for name in sorted(to_install):
            ver = lock_map.get(name)
            v = ver.version if ver else "?"
            console.print(f"  [dim]Would install:[/dim] {name} v{v}")
        for name in sorted(to_remove):
            console.print(f"  [dim]Would remove:[/dim]  {name}")
        console.print(
            f"\n[yellow]Dry run complete.[/yellow] "
            f"{len(to_install)} install, {len(to_remove)} remove."
        )
        return

    async def _sync() -> None:
        from gdpm.utils.local import sync_local_plugins

        # Step 1: Sync local plugins first
        local_synced = sync_local_plugins(root, addons_dir)
        if local_synced:
            console.print(
                f"[green]✓[/green] Synced {len(local_synced)} local plugin(s)"
            )

        store = StoreClient()
        cache_dir = root / ".gdpm" / "cache"
        cache = FileCache(cache_dir)
        manager = PluginManager(addons_dir, cache, store)

        installed = 0
        removed = 0
        errors: list[str] = []

        try:
            updated_entries: dict[str, LockEntry] = {}

            for name in sorted(to_install):
                entry = lock_map.get(name)
                deps = all_deps.get(name)
                dest_path = deps.path if deps else ""

                if not entry:
                    if deps:
                        search_results = await store.search(name, limit=5)
                        exact = next(
                            (r for r in search_results if r.slug == name), None
                        )
                        if exact:
                            publisher = exact.publisher_slug
                            try:
                                zip_path, ver = await manager.download(publisher, name)
                                manager.install_from_zip(
                                    zip_path, name, publisher, dest_path
                                )
                                installed += 1
                                console.print(
                                    f"[green]✓[/green] Installed "
                                    f"[bold]{name}[/bold] {ver}"
                                )
                                updated_entries[name] = LockEntry(
                                    name=name,
                                    version=ver,
                                    source=f"store+{publisher}/{name}",
                                )
                            except Exception as e:
                                errors.append(f"Failed to install {name}: {e}")
                        else:
                            errors.append(f"Plugin '{name}' not found in Store")
                    continue

                publisher = entry.source.replace("store+", "").split("/")[0]
                try:
                    zip_path, ver = await manager.download(
                        publisher, name, entry.version.lstrip("v")
                    )
                    manager.install_from_zip(zip_path, name, publisher, dest_path)
                    installed += 1
                    console.print(
                        f"[green]✓[/green] Installed "
                        f"[bold]{name}[/bold] {entry.version}"
                    )
                    updated_entries[name] = LockEntry(
                        name=name,
                        version=entry.version,
                        source=entry.source,
                    )
                except Exception as e:
                    errors.append(f"Failed to install {name}: {e}")

            for name in sorted(to_remove):
                manager.remove(name)
                removed += 1
                console.print(f"[green]✓[/green] Removed [bold]{name}[/bold]")

            if updated_entries:
                lock_map.update(updated_entries)
                write_lockfile(list(lock_map.values()), lock_path)

        finally:
            await manager.close()

        console.print()
        summary = []
        if installed:
            summary.append(f"{installed} installed")
        if removed:
            summary.append(f"{removed} removed")
        if errors:
            summary.append(f"{len(errors)} errors")

        console.print(f"[green]✓[/green] Sync complete: {', '.join(summary)}")

        for err in errors:
            console.print(f"  [red]✗[/red] {err}")

    asyncio.run(_sync())


def _generate_lock(
    root: Path,
    config: ProjectConfig,
    lock_path: Path,
) -> None:
    async def _gen() -> None:
        store = StoreClient()
        entries: list[LockEntry] = []

        try:
            all_deps = {**config.dependencies, **config.dev_dependencies}

            for name, dep in all_deps.items():
                if dep.publisher_slug:
                    publisher = dep.publisher_slug
                else:
                    search_results = await store.search(name, limit=5)
                    exact = next((r for r in search_results if r.slug == name), None)
                    if not exact:
                        continue
                    publisher = exact.publisher_slug

                versions = await store.get_versions(publisher, name)
                if not versions:
                    continue

                ver = versions[0]["version"]
                entries.append(
                    LockEntry(
                        name=name,
                        version=ver,
                        source=f"store+{publisher}/{name}",
                    )
                )
        finally:
            await store.close()

        if entries:
            write_lockfile(entries, lock_path)
            console.print(
                f"[green]✓[/green] Generated lock file with {len(entries)} packages"
            )

    asyncio.run(_gen())
