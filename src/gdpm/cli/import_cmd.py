"""gdpm import command."""

from __future__ import annotations

import asyncio
import json
import zipfile
from pathlib import Path

import click
from rich.console import Console

from gdpm.cache.file_cache import FileCache
from gdpm.cli.common import require_project
from gdpm.cli.options import yes_option
from gdpm.config.project import read_project_config, write_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.dependency import Dependency
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient
from gdpm.utils.local import LOCAL_DIR_NAME, tag_plugin

console = Console()


@click.command()
@click.argument("file", type=click.Path(exists=True))
@yes_option
def import_cmd(file: str, yes: bool) -> None:
    """Import plugins from a zip archive."""
    root = require_project()
    zip_path = Path(file)

    if not zipfile.is_zipfile(zip_path):
        console.print(f"[red]Error:[/red] '{file}' is not a valid zip file")
        raise SystemExit(1)

    with zipfile.ZipFile(zip_path, "r") as zf:
        if "manifest.json" not in zf.namelist():
            console.print("[red]Error:[/red] No manifest.json found in zip")
            raise SystemExit(1)

        manifest = json.loads(zf.read("manifest.json"))
        plugins = manifest.get("plugins", [])

    console.print(f"Importing {len(plugins)} plugin(s)...\n")

    config = read_project_config(root / "gdproject.toml")
    addons_dir = root / config.addons_dir
    local_dir = root / LOCAL_DIR_NAME
    lock_entries = {e.name: e for e in read_lockfile(find_lockfile(root))}

    store_plugins: list[dict[str, str]] = []
    local_plugins: list[dict[str, str]] = []

    for p in plugins:
        if p.get("type") == "local":
            local_plugins.append(p)
        else:
            store_plugins.append(p)

    imported = 0
    errors: list[str] = []
    lock_updates: dict[str, LockEntry] = {}

    # Import store plugins
    if store_plugins:

        async def _import_store() -> None:
            nonlocal imported
            store = StoreClient()
            cache = FileCache(root / ".gdpm" / "cache")
            manager = PluginManager(addons_dir, cache, store)

            try:
                for p in store_plugins:
                    name = p["name"]
                    publisher = p.get("publisher", "")
                    version = p.get("version", "")

                    # Check if already installed
                    existing = config.dependencies.get(name)
                    if existing:
                        entry = lock_entries.get(name)
                        if entry and entry.version == version:
                            console.print(
                                f"  [dim]○ {name} {version} "
                                "(already installed, skipped)[/dim]"
                            )
                            continue
                        # Different version - ask user
                        if not yes:
                            old_ver = entry.version if entry else "?"
                            if not console.input(
                                f"  [yellow]?[/yellow] {name} "
                                f"v{old_ver} → v{version}? (y/n): "
                            ).strip().lower().startswith("y"):
                                console.print(
                                    f"  [dim]○ {name} (skipped)[/dim]"
                                )
                                continue

                    if not publisher:
                        source = p.get("source", "")
                        if "/" in source:
                            publisher = source.split("/")[-2]

                    if not publisher:
                        errors.append(
                            f"Cannot resolve publisher for '{name}'"
                        )
                        continue

                    try:
                        ver_to_get = version.lstrip("v") if version else ""
                        zip_dl, ver = await manager.download(
                            publisher, name, ver_to_get
                        )
                        manager.install_from_zip(zip_dl, name, publisher)
                        lock_updates[name] = LockEntry(
                            name=name,
                            version=ver,
                            source=f"store+{publisher}/{name}",
                        )

                        # Update config
                        dep = Dependency.from_spec(
                            name, ver, publisher_slug=publisher
                        )
                        config.dependencies[name] = dep

                        imported += 1
                        console.print(
                            f"[green]✓[/green] Installed "
                            f"[bold]{name}[/bold] {ver}"
                        )
                    except Exception as e:
                        errors.append(f"Failed to install {name}: {e}")
            finally:
                await store.close()

        asyncio.run(_import_store())

    # Import local plugins
    for p in local_plugins:
        name = p["name"]
        zip_file = p.get("file", "")

        # Skip if already installed
        if name in config.dependencies:
            if not yes:
                if not console.input(
                    f"  [yellow]?[/yellow] {name} "
                    "already installed. Overwrite? (y/n): "
                ).strip().lower().startswith("y"):
                    console.print(f"  [dim]○ {name} (skipped)[/dim]")
                    continue
            else:
                console.print(
                    f"  [yellow]![/yellow] {name} "
                    "already installed, overwriting..."
                )

        if zip_file and zip_file in zf.namelist():
            local_dir.mkdir(parents=True, exist_ok=True)
            local_zip = local_dir / f"{name}.zip"

            with (
                zipfile.ZipFile(zip_path, "r") as zf_outer,
                zf_outer.open(zip_file) as src,
            ):
                local_zip.write_bytes(src.read())

            import shutil

            dest = addons_dir / name
            if dest.exists():
                shutil.rmtree(dest)

            with zipfile.ZipFile(local_zip, "r") as local_zf:
                local_zf.extractall(dest)

            tag_plugin(addons_dir, name)

            lock_updates[name] = LockEntry(name=name, version="local", source="local")

            dep = Dependency.from_spec(name, "*", is_local=True)
            config.dependencies[name] = dep

            imported += 1
            console.print(f"[green]✓[/green] Installed [bold]{name}[/bold] (local)")

    # Update config and lock
    if imported:
        write_project_config(config, root / "gdproject.toml")
        update_lockfile(find_lockfile(root), lock_updates)

        console.print()
        console.print(f"[green]✓[/green] Imported {imported} plugin(s)")
        console.print("  Updated [cyan]gdproject.toml[/cyan]")
        console.print("  Updated [cyan]gdpm.lock[/cyan]")

    if errors:
        for err in errors:
            console.print(f"[red]✗[/red] {err}")
