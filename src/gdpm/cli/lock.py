"""gdpm lock command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console

from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, write_lockfile
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient

console = Console()


@click.command()
@click.option("--check", is_flag=True, help="Check if lock file is up to date")
def lock(check: bool) -> None:
    """Generate or update the lock file."""

    async def _lock() -> None:
        root = require_project()
        config_path = root / "gdproject.toml"
        config = read_project_config(config_path)
        lock_path = find_lockfile(root)

        store = StoreClient()
        entries: list[LockEntry] = []
        errors: list[str] = []

        try:
            console.print("Resolving dependencies...")

            all_deps = {**config.dependencies, **config.dev_dependencies}

            for name, dep in all_deps.items():
                # Local plugins - skip API lookup
                if dep.is_local:
                    console.print(f"  {name} (local)")
                    entries.append(
                        LockEntry(
                            name=name,
                            version="local",
                            source="local",
                        )
                    )
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
                versions = await store.get_versions(publisher, name)

                if not versions:
                    errors.append(f"No versions found for '{name}'")
                    continue

                matched = None
                for v in versions:
                    api_ver = v["version"].lstrip("v")
                    if dep.constraint.matches(
                        __import__("gdpm.models.version", fromlist=["Version"]).Version(
                            api_ver
                        )
                    ):
                        matched = v
                        break

                if not matched:
                    errors.append(f"No version of '{name}' satisfies {dep.constraint}")
                    continue

                ver = matched["version"]
                source = f"store+{publisher}/{name}"
                console.print(f"  {name} {ver}")

                entries.append(
                    LockEntry(
                        name=name,
                        version=ver,
                        source=source,
                    )
                )

        finally:
            await store.close()

        if errors:
            for err in errors:
                console.print(f"[red]✗[/red] {err}")

        if entries:
            write_lockfile(entries, lock_path)
            console.print(
                f"[green]✓[/green] Lock file updated: {len(entries)} packages"
            )
        elif not errors:
            console.print("[yellow]![/yellow] No dependencies to lock")

    asyncio.run(_lock())
