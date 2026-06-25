"""gdpm update command."""

from __future__ import annotations

import asyncio

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.context import get_project_context, get_services
from gdpm.cli.options import yes_option
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.lock import LockEntry
from gdpm.utils.version import normalize_version


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm update", "Update all plugins"),
        ("gdpm update limbo-ai", "Update specific plugin"),
        ("gdpm update --check", "Preview updates"),
        ("gdpm update --latest", "Ignore version constraints"),
    ],
)
@click.argument("plugins", nargs=-1)
@click.option("--latest", is_flag=True, help="Ignore version constraints")
@click.option(
    "-dr",
    "--check",
    "--dry-run",
    is_flag=True,
    help="Check for updates without applying",
)
@yes_option
def update(plugins: tuple[str, ...], latest: bool, check: bool, yes: bool) -> None:
    """Update plugins to newer versions."""

    async def _update() -> None:
        ctx = get_project_context()

        if plugins:
            targets = {p.split("/")[-1] for p in plugins}
        else:
            targets = set(ctx.all_deps.keys())

        svc = get_services(ctx)
        updates: list[dict[str, str]] = []
        errors: list[str] = []

        try:
            console.print("Checking for updates...")

            for name in targets:
                dep = ctx.all_deps.get(name)
                if not dep:
                    errors.append(f"Plugin '{name}' not in dependencies")
                    continue

                # Skip local plugins
                if dep.is_local:
                    console.print(f"  [dim]Skipping {name} (local plugin)[/dim]")
                    continue

                # Resolve publisher
                if dep.publisher_slug:
                    publisher = dep.publisher_slug
                else:
                    from gdpm.store.utils import resolve_publisher

                    resolved = await resolve_publisher(svc.store, name)
                    if not resolved.found:
                        errors.append(resolved.error)
                        continue
                    publisher = resolved.publisher

                # Get versions
                try:
                    versions = await svc.store.get_versions(publisher, name)
                except Exception as e:
                    errors.append(f"Failed to fetch versions for '{name}': {e}")
                    continue

                if not versions:
                    errors.append(f"No versions found for '{name}'")
                    continue

                # Find current version
                current = ctx.lock_map.get(name)
                current_ver = current.version.lstrip("v") if current else ""

                # Find latest compatible version
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
                if current_ver and normalize_version(new_ver) == normalize_version(
                    current_ver
                ):
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
            await svc.store.close()

        if not updates:
            console.print("[green]✓[/green] All plugins are up to date.")
            return

        console.print(f"\n{len(updates)} update(s) available:\n")
        for u in updates:
            console.print(
                f"  [cyan]{u['name']}[/cyan]  "
                f"{u['old_version']} → [green]{u['new_version']}[/green]"
            )

        if check:
            console.print("\n[yellow]Dry run complete.[/yellow]")
            return

        # Apply updates
        svc2 = get_services(ctx)
        applied = 0
        lock_updates: dict[str, LockEntry] = {}

        try:
            for u in updates:
                try:
                    zip_path, _ver = await svc2.manager.download(
                        u["publisher"],
                        u["name"],
                        u["new_version"].lstrip("v"),
                    )
                    svc2.manager.install_from_zip(zip_path, u["name"], u["publisher"])
                    lock_updates[u["name"]] = LockEntry(
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
            await svc2.store.close()

        if applied:
            update_lockfile(ctx.lock_path, lock_updates)
            console.print(f"\n[green]✓[/green] Updated {applied} plugin(s)")

    with console.status("Loading...", spinner="dots"):
        asyncio.run(_update())
