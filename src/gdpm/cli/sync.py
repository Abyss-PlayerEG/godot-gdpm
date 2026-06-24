"""gdpm sync command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console

from gdpm.cli.context import get_project_context, get_services
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.lock import LockEntry
from gdpm.store.utils import resolve_publisher
from gdpm.utils.tag import scan_addons

console = Console()


@click.command()
@click.option("--frozen", is_flag=True, help="Strict mode for CI")
@click.option(
    "-dr", "--check", "--dry-run", is_flag=True, help="Preview changes without applying"
)
@click.option("--no-cache", is_flag=True, help="Don't use local cache")
def sync(frozen: bool, check: bool, no_cache: bool) -> None:
    """Sync addons/ directory to lock file state."""
    ctx = get_project_context()

    # Separate local and online plugins
    local_names = {n for n, d in ctx.all_deps.items() if d.is_local}
    online_names = set(ctx.all_deps.keys()) - local_names

    # Check what's installed via tag files
    installed_by_dep: set[str] = set()
    for _, tag in scan_addons(ctx.addons_dir):
        for name in set(ctx.all_deps.keys()):
            if tag.source.endswith(f"/{name}") or tag.slug == name:
                installed_by_dep.add(name)

    to_install = online_names - installed_by_dep

    # Check what needs to be removed
    to_remove: set[str] = set()
    for _, tag in scan_addons(ctx.addons_dir):
        if tag.source.endswith(f"/{tag.slug}") and tag.slug not in ctx.all_deps:
            to_remove.add(tag.slug)

    if not to_install and not to_remove:
        console.print("[green]✓[/green] Everything is up to date. Nothing to do.")
        return

    if check:
        for name in sorted(to_install):
            entry = ctx.lock_map.get(name)
            v = entry.version if entry else "?"
            console.print(f"  [dim]Would install:[/dim] {name} {v}")
        for name in sorted(to_remove):
            console.print(f"  [dim]Would remove:[/dim]  {name}")
        console.print(
            f"\n[yellow]Dry run complete.[/yellow] "
            f"{len(to_install)} install, {len(to_remove)} remove."
        )
        return

    async def _sync() -> None:
        from gdpm.utils.local import sync_local_plugins

        # Step 1: Sync local plugins
        local_synced = sync_local_plugins(ctx.root, ctx.addons_dir)
        if local_synced:
            console.print(
                f"[green]✓[/green] Synced {len(local_synced)} local plugin(s)"
            )

        svc = get_services(ctx)
        installed = 0
        removed = 0
        errors: list[str] = []
        lock_updates: dict[str, LockEntry] = {}

        try:
            for name in sorted(to_install):
                entry = ctx.lock_map.get(name)
                deps = ctx.all_deps.get(name)
                dest_path = deps.path if deps else ""

                if not entry:
                    if deps:
                        resolved = await resolve_publisher(svc.store, name)
                        if resolved.found:
                            try:
                                zip_path, ver = await svc.manager.download(
                                    resolved.publisher, name
                                )
                                svc.manager.install_from_zip(
                                    zip_path, name, resolved.publisher, dest_path
                                )
                                installed += 1
                                console.print(
                                    f"[green]✓[/green] Installed "
                                    f"[bold]{name}[/bold] {ver}"
                                )
                                lock_updates[name] = LockEntry(
                                    name=name,
                                    version=ver,
                                    source=f"store+{resolved.publisher}/{name}",
                                )
                            except Exception as e:
                                errors.append(f"Failed to install {name}: {e}")
                        else:
                            errors.append(f"Plugin '{name}' not found in Store")
                    continue

                publisher = entry.source.replace("store+", "").split("/")[0]
                try:
                    zip_path, ver = await svc.manager.download(
                        publisher, name, entry.version.lstrip("v")
                    )
                    svc.manager.install_from_zip(zip_path, name, publisher, dest_path)
                    installed += 1
                    console.print(
                        f"[green]✓[/green] Installed "
                        f"[bold]{name}[/bold] {entry.version}"
                    )
                    lock_updates[name] = LockEntry(
                        name=name,
                        version=entry.version,
                        source=entry.source,
                    )
                except Exception as e:
                    errors.append(f"Failed to install {name}: {e}")

            for name in sorted(to_remove):
                svc.manager.remove(name)
                removed += 1
                console.print(f"[green]✓[/green] Removed [bold]{name}[/bold]")

            # Update lock file
            if local_synced:
                for name in local_synced:
                    lock_updates[name] = LockEntry(
                        name=name, version="local", source="local"
                    )

            if lock_updates or to_remove:
                update_lockfile(ctx.lock_path, lock_updates, list(to_remove))

        finally:
            await svc.store.close()

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
