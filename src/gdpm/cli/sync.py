"""gdpm sync command."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import click
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.context import get_project_context, get_services
from gdpm.cli.options import yes_option
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.lock import LockEntry
from gdpm.store.utils import resolve_publisher
from gdpm.utils.tag import scan_addons

if TYPE_CHECKING:
    from pathlib import Path

MAX_PARALLEL = 5


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm sync", "Sync all plugins"),
        ("gdpm sync --check", "Preview changes without applying"),
        ("gdpm sync --frozen", "Strict mode for CI"),
    ],
)
@click.option("--frozen", is_flag=True, help="Strict mode for CI")
@click.option(
    "-dr",
    "--check",
    "--dry-run",
    is_flag=True,
    help="Preview changes without applying",
)
@click.option("-nc", "--no-cache", is_flag=True, help="Don't use local cache")
@yes_option
def sync(frozen: bool, check: bool, no_cache: bool, yes: bool) -> None:
    """Sync addons/ directory to lock file state."""
    ctx = get_project_context()

    if frozen and not ctx.lock_path.exists():
        console.print("[red]Error:[/red] No lock file found. Run 'gdpm lock' first.")
        raise SystemExit(1)

    local_names = {n for n, d in ctx.all_deps.items() if d.is_local}
    online_names = set(ctx.all_deps.keys()) - local_names

    installed_by_dep: set[str] = set()
    if ctx.addons_dir.exists():
        for _, tag in scan_addons(ctx.addons_dir):
            for name in set(ctx.all_deps.keys()):
                if tag.source.endswith(f"/{name}") or tag.slug == name:
                    installed_by_dep.add(name)

    to_install = online_names - installed_by_dep

    to_remove: set[str] = set()
    if ctx.addons_dir.exists():
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

        local_synced = sync_local_plugins(ctx.root, ctx.addons_dir)
        if local_synced:
            console.print(
                f"[green]✓[/green] Synced {len(local_synced)} local plugin(s)"
            )

        svc = get_services(ctx)
        errors: list[str] = []
        lock_updates: dict[str, LockEntry] = {}

        if no_cache:
            svc.manager._cache.clean()
            console.print("[dim]Cache cleared.[/dim]")

        # Prepare download tasks
        download_tasks: list[tuple[str, str, str]] = []

        for name in sorted(to_install):
            entry = ctx.lock_map.get(name)
            deps = ctx.all_deps.get(name)
            dest_path = deps.path if deps else ""

            if entry:
                publisher = entry.source.replace("store+", "").split("/")[0]
                download_tasks.append((name, publisher, entry.version.lstrip("v")))
            elif deps:
                resolved = await resolve_publisher(svc.store, name)
                if resolved.found:
                    download_tasks.append((name, resolved.publisher, ""))
                else:
                    errors.append(f"Plugin '{name}' not found in Store")

        # Download in parallel
        if download_tasks:
            console.print(
                f"\nDownloading {len(download_tasks)} plugin(s) "
                f"(max {MAX_PARALLEL} parallel)...\n"
            )

            semaphore = asyncio.Semaphore(MAX_PARALLEL)
            progress = Progress(
                TextColumn("[bold blue]{task.fields[name]}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            )

            async def download_one(
                name: str, publisher: str, version: str
            ) -> tuple[str, str, str, bool, Path | None]:
                async with semaphore:
                    task_id = progress.add_task("download", name=name, total=None)

                    def on_progress(
                        current: int,
                        total: int,
                        speed: float,
                        _task: TaskID = task_id,
                    ) -> None:
                        if progress.tasks[_task].total is None:
                            progress.update(_task, total=total)
                        progress.update(_task, completed=current)

                    try:
                        zip_path, ver = await svc.manager.download(
                            publisher,
                            name,
                            version,
                            on_progress=on_progress,
                        )
                        return name, ver, publisher, True, zip_path
                    except Exception:
                        return name, "", publisher, False, None

            with progress:
                results = await asyncio.gather(
                    *[download_one(n, p, v) for n, p, v in download_tasks]
                )

            # Install downloaded plugins
            for name, ver, publisher, success, zip_path in results:
                if not success or not zip_path:
                    errors.append(f"Failed to download {name}")
                    continue

                try:
                    deps = ctx.all_deps.get(name)
                    dest_path = deps.path if deps else ""
                    svc.manager.install_from_zip(zip_path, name, publisher, dest_path)
                    lock_updates[name] = LockEntry(
                        name=name,
                        version=ver,
                        source=f"store+{publisher}/{name}",
                    )
                    console.print(
                        f"  [green]✓[/green] Installed [bold]{name}[/bold] {ver}"
                    )
                except Exception as e:
                    errors.append(f"Failed to install {name}: {e}")

        # Remove plugins
        for name in sorted(to_remove):
            svc.manager.remove(name)
            console.print(f"  [green]✓[/green] Removed [bold]{name}[/bold]")

        # Update lock file
        if local_synced:
            for name in local_synced:
                lock_updates[name] = LockEntry(
                    name=name, version="local", source="local"
                )

        if not frozen and (lock_updates or to_remove):
            update_lockfile(ctx.lock_path, lock_updates, list(to_remove))

        await svc.store.close()

        summary = []
        installed_count = len(lock_updates)
        removed_count = len(to_remove)
        if installed_count:
            summary.append(f"{installed_count} installed")
        if removed_count:
            summary.append(f"{removed_count} removed")
        if errors:
            summary.append(f"{len(errors)} errors")

        console.print(f"[green]✓[/green] Sync complete: {', '.join(summary)}")

        for err in errors:
            console.print(f"  [red]✗[/red] {err}")

    with console.status("Loading...", spinner="dots"):
        asyncio.run(_sync())
