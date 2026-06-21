"""gdpm add command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console

from gdpm.cache.file_cache import FileCache
from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config, write_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile, write_lockfile
from gdpm.models.dependency import Dependency
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient

console = Console()


@click.command()
@click.argument("plugins", nargs=-1, required=True)
@click.option("--dev", is_flag=True, help="Add as dev dependency")
@click.option("--no-sync", is_flag=True, help="Only update config, don't install")
def add(plugins: tuple[str, ...], dev: bool, no_sync: bool) -> None:
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
                    template_tags = {"template", "starterkit", "demo", "project"}
                    if any(t.lower() in template_tags for t in detail.tags):
                        errors.append(
                            f"'{slug}' is a project template, not an addon. "
                            "Use 'gdpm search' to find addons instead."
                        )
                        continue
                except Exception:
                    pass

                try:
                    result = await manager.install(publisher, slug)
                    results.append(result)
                except Exception as e:
                    if "404" in str(e):
                        search_results = await store.search(slug, limit=5)
                        exact = next(
                            (r for r in search_results if r.slug == slug), None
                        )
                        if exact:
                            errors.append(
                                f"Plugin '{slug}' not found at '{publisher}'. "
                                f"Did you mean: {exact.publisher_slug}/{slug}?"
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
