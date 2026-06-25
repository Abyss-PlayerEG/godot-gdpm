"""gdpm lock command."""

from __future__ import annotations

import asyncio

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.context import get_project_context
from gdpm.lockfile.lock import write_lockfile
from gdpm.models.lock import LockEntry
from gdpm.store.utils import resolve_publisher


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm lock", "Generate lock file"),
        ("gdpm lock --check", "Check if lock file is up to date"),
    ],
)
@click.option("--check", is_flag=True, help="Check if lock file is up to date")
def lock(check: bool) -> None:
    """Generate or update the lock file."""

    async def _lock() -> None:
        ctx = get_project_context()
        store = ctx.store if hasattr(ctx, "store") else None

        from gdpm.store.client import StoreClient

        store = StoreClient()
        entries: list[LockEntry] = []
        errors: list[str] = []

        try:
            console.print("Resolving dependencies...")

            for name, dep in ctx.all_deps.items():
                # Local plugins
                if dep.is_local:
                    console.print(f"  {name} (local)")
                    entries.append(
                        LockEntry(name=name, version="local", source="local")
                    )
                    continue

                # Resolve publisher
                if dep.publisher_slug:
                    publisher = dep.publisher_slug
                else:
                    resolved = await resolve_publisher(store, name)
                    if not resolved.found:
                        errors.append(resolved.error)
                        continue
                    publisher = resolved.publisher

                # Get versions
                versions = await store.get_versions(publisher, name)
                if not versions:
                    errors.append(f"No versions found for '{name}'")
                    continue

                # Match version
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

                entries.append(LockEntry(name=name, version=ver, source=source))

        finally:
            await store.close()

        if errors:
            for err in errors:
                console.print(f"[red]✗[/red] {err}")

        if entries:
            write_lockfile(entries, ctx.lock_path)
            console.print(
                f"[green]✓[/green] Lock file updated: {len(entries)} packages"
            )
        elif not errors:
            console.print("[yellow]![/yellow] No dependencies to lock")

    asyncio.run(_lock())
