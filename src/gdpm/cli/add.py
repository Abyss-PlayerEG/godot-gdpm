"""gdpm add command."""

from __future__ import annotations

import asyncio
from pathlib import Path

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
from gdpm.cli.common import console, is_template
from gdpm.cli.context import get_project_context, get_services
from gdpm.cli.options import yes_option
from gdpm.config.project import write_project_config
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.dependency import Dependency
from gdpm.models.lock import LockEntry
from gdpm.store.utils import resolve_publisher


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm add limbo-ai", "Add plugin from Godot Store"),
        ("gdpm add limofeus/limbo-ai", "Add with publisher/slug"),
        ("gdpm add limbo-ai@1.5.0", "Add specific version"),
        ("gdpm add limbo-ai@^1.0.0", "Add with version constraint"),
        ("gdpm add --dev gdunit4", "Add as dev dependency"),
        ("gdpm add --local", "Pack all local plugins"),
        ("gdpm add --local plugin.zip", "Install from zip file"),
    ],
)
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
        ctx = get_project_context()
        svc = get_services(ctx)

        results: list[dict[str, str]] = []
        errors: list[str] = []
        lock_updates: dict[str, LockEntry] = {}

        try:
            for plugin_spec in plugins:
                name, version_constraint = _parse_spec(plugin_spec)

                # Check if already in dependencies
                if (
                    name in ctx.config.dependencies
                    or name in ctx.config.dev_dependencies
                ):
                    console.print(
                        f"[yellow]![/yellow] [bold]{name}[/bold] "
                        "already in dependencies. Use 'gdpm update' to update."
                    )
                    continue

                # Resolve publisher
                resolved = await resolve_publisher(svc.store, name)
                if not resolved.found:
                    errors.append(resolved.error)
                    continue

                publisher = resolved.publisher
                slug = resolved.slug

                # Check if template
                try:
                    detail = await svc.store.get_plugin(publisher, slug)
                    if is_template(detail.tags):
                        errors.append(f"'{slug}' is a project template, not an addon.")
                        continue
                except Exception:
                    pass

                # Show version info
                versions = await svc.store.get_versions(publisher, slug)
                if versions:
                    # Find the version that matches the constraint
                    target_ver = versions[0].get("version", "")
                    if version_constraint:
                        from gdpm.models.version import Version, VersionConstraint

                        constraint = VersionConstraint(version_constraint)
                        for v in versions:
                            api_ver = v.get("version", "").lstrip("v")
                            try:
                                if constraint.matches(Version(api_ver)):
                                    target_ver = v.get("version", "")
                                    break
                            except Exception:
                                pass

                    if target_ver.startswith(("v", "V")):
                        ver_display = target_ver
                    else:
                        ver_display = f"v{target_ver}"
                    console.print(f"  [dim]{ver_display}[/dim]")

                # Download and install
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

                        ver = (
                            version_constraint.lstrip("v") if version_constraint else ""
                        )
                        zip_path, ver = await svc.manager.download(
                            publisher,
                            slug,
                            version=ver,
                            on_progress=on_progress,
                        )

                    svc.manager.install_from_zip(zip_path, slug, publisher)

                    result = {
                        "name": slug,
                        "version": ver,
                        "source": f"store+{publisher}/{slug}",
                    }
                    results.append(result)

                    lock_updates[slug] = LockEntry(
                        name=slug,
                        version=ver,
                        source=f"store+{publisher}/{slug}",
                    )

                except Exception as e:
                    if "404" in str(e):
                        search_results = await svc.store.search(slug, limit=5)
                        exact = next(
                            (r for r in search_results if r.slug == slug),
                            None,
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

                # Update config
                dep = Dependency.from_spec(
                    slug,
                    version_constraint or result["version"],
                    publisher_slug=publisher,
                    is_dev=dev,
                )

                if dev:
                    ctx.config.dev_dependencies[slug] = dep
                else:
                    ctx.config.dependencies[slug] = dep

        finally:
            await svc.store.close()

        if results:
            write_project_config(ctx.config, ctx.config_path)
            update_lockfile(ctx.lock_path, lock_updates)

            added_lines = []
            for r in results:
                added_lines.append(
                    f"[green]✓[/green] Added [bold]{r['name']}[/bold] {r['version']}"
                )
            added_lines.append("  Updated [cyan]gdproject.toml[/cyan]")
            added_lines.append("  Updated [cyan]gdpm.lock[/cyan]")
            console.print("\n".join(added_lines))

        if errors:
            for err in errors:
                console.print(f"[red]✗[/red] {err}")

        if not results and errors:
            raise SystemExit(1)

    asyncio.run(_add())


def _add_local(plugins: tuple[str, ...], yes: bool = False) -> None:
    """Pack local plugins to gdpm-local/ or install from zip."""
    from gdpm.lockfile.lock import find_lockfile, read_lockfile, write_lockfile
    from gdpm.models.lock import LockEntry
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
    from gdpm.utils.zip import extract_full_zip

    ctx = get_project_context()
    local_dir = ctx.root / LOCAL_DIR_NAME

    # Separate zip files and directory names
    zip_files: list[Path] = []
    dir_names: list[str] = []

    for item in plugins:
        p = Path(item)
        if p.suffix == ".zip" and p.exists():
            zip_files.append(p)
        else:
            dir_names.append(item)

    # Install from zip files
    for zip_path in zip_files:
        slug = zip_path.stem
        dest = ctx.addons_dir / slug

        console.print(f"Installing from [cyan]{zip_path.name}[/cyan]...")
        extract_full_zip(zip_path, dest)
        tag_plugin(ctx.addons_dir, slug)

        # Copy zip to gdpm-local/ (skip if already there)
        local_dir.mkdir(parents=True, exist_ok=True)
        local_zip = local_dir / zip_path.name
        import shutil

        if zip_path.resolve() != local_zip.resolve():
            shutil.copy2(zip_path, local_zip)

        # Update config
        dep = Dependency.from_spec(slug, "*", is_local=True, is_dev=False)
        ctx.config.dependencies[slug] = dep

        # Update lock
        lock_path = find_lockfile(ctx.root)
        lock_entries = {e.name: e for e in read_lockfile(lock_path)}
        lock_entries[slug] = LockEntry(
            name=slug,
            version="local",
            source="local",
        )
        write_lockfile(list(lock_entries.values()), lock_path)

        console.print(f"[green]✓[/green] Installed [bold]{slug}[/bold] from zip")

    # Handle directory names (existing logic)
    if dir_names:
        targets = dir_names
    else:
        untagged = scan_untagged_or_local_plugins(ctx.addons_dir)
        if not untagged:
            if not zip_files:
                console.print("[dim]No local plugins found in addons/[/dim]")
            return
        targets = [p.name for p in untagged]

    if not targets:
        if not zip_files:
            console.print("[dim]No plugins to pack.[/dim]")
        return

    hashes = load_hashes(ctx.root)
    console.print(f"Scanning {len(targets)} plugin(s)...\n")

    packed = 0
    skipped = 0
    renamed = 0

    for name in targets:
        plugin_dir = ctx.addons_dir / name
        if not plugin_dir.exists():
            console.print(f"[red]✗[/red] Plugin directory not found: {name}")
            continue

        content_hash = compute_dir_hash(plugin_dir)

        existing_name = find_matching_hash(hashes, content_hash)

        if existing_name and existing_name != name:
            old_zip = local_dir / f"{existing_name}.zip"
            new_zip = local_dir / f"{name}.zip"

            if old_zip.exists():
                old_zip.rename(new_zip)
            hashes.pop(existing_name, None)
            hashes[name] = content_hash
            tag_plugin(ctx.addons_dir, name)

            if existing_name in ctx.config.dependencies:
                dep = ctx.config.dependencies.pop(existing_name)
                ctx.config.dependencies[name] = dep

            console.print(
                f"[green]✓[/green] Renamed [bold]{existing_name}[/bold] "
                f"→ [bold]{name}[/bold]"
            )
            renamed += 1
            continue

        zip_exists = (local_dir / f"{name}.zip").exists()
        is_registered = (
            name in ctx.config.dependencies or name in ctx.config.dev_dependencies
        )

        if not zip_exists or not is_registered:
            pass
        elif name in hashes and hashes[name] == content_hash:
            console.print(f"  [dim]○ {name}: unchanged → skipped[/dim]")
            skipped += 1
            continue

        tag_plugin(ctx.addons_dir, name)
        pack_plugin(ctx.addons_dir, name, local_dir)
        hashes[name] = content_hash

        dep = Dependency.from_spec(name, "*", is_local=True, is_dev=False)
        ctx.config.dependencies[name] = dep

        console.print(
            f"[green]✓[/green] Packed [bold]{name}[/bold] → {LOCAL_DIR_NAME}/{name}.zip"
        )
        packed += 1

    if packed or renamed:
        save_hashes(ctx.root, hashes)
        write_project_config(ctx.config, ctx.config_path)

        lock_path = find_lockfile(ctx.root)
        lock_entries = {e.name: e for e in read_lockfile(lock_path)}

        for name in targets:
            plugin_dir = ctx.addons_dir / name
            if plugin_dir.exists():
                lock_entries[name] = LockEntry(
                    name=name,
                    version="local",
                    source="local",
                )

        write_lockfile(list(lock_entries.values()), lock_path)

        if packed:
            console.print(f"  Packed: {packed}")
        if renamed:
            console.print(f"  Renamed: {renamed}")
        if skipped:
            console.print(f"  Skipped: {skipped}")
        console.print(
            "  Updated [cyan]gdproject.toml[/cyan]"
            "  Updated [cyan]gdpm.lock[/cyan]"
            f"  Updated [cyan]{LOCAL_DIR_NAME}/.hashes[/cyan]"
        )


def _parse_spec(spec: str) -> tuple[str, str]:
    if "@" in spec:
        name, constraint = spec.split("@", 1)
        return name, constraint
    return spec, ""
