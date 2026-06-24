"""gdpm export command."""

from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import click
from rich.console import Console

from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.utils.local import LOCAL_DIR_NAME
from gdpm.utils.tag import scan_addons

console = Console()


@click.command()
@click.option("-o", "--output", default="", help="Output file path")
def export(output: str) -> None:
    """Export plugins to a zip archive."""
    root = require_project()
    config = read_project_config(root / "gdproject.toml")
    lock_entries = {e.name: e for e in read_lockfile(find_lockfile(root))}
    local_dir = root / LOCAL_DIR_NAME

    all_deps = {**config.dependencies, **config.dev_dependencies}

    # Build manifest - start with declared dependencies
    plugins: list[dict[str, str]] = []
    local_files: list[str] = []
    seen: set[str] = set()

    for name, dep in all_deps.items():
        entry = lock_entries.get(name)
        seen.add(name)

        if dep.is_local:
            local_zip = local_dir / f"{name}.zip"
            if local_zip.exists():
                local_files.append(name)
                plugins.append({
                    "name": name,
                    "version": "local",
                    "source": "local",
                    "type": "local",
                    "file": f"local-plugins/{name}.zip",
                })
        else:
            plugins.append({
                "name": name,
                "version": entry.version if entry else str(dep.constraint),
                "source": entry.source if entry else "",
                "publisher": dep.publisher_slug,
                "type": "store",
            })

    # Also scan addons/ for installed plugins not in config
    for _, tag in scan_addons(root / config.addons_dir):
        if tag.slug in seen:
            continue
        seen.add(tag.slug)

        if tag.is_local:
            local_zip = local_dir / f"{tag.slug}.zip"
            if local_zip.exists():
                local_files.append(tag.slug)
                plugins.append({
                    "name": tag.slug,
                    "version": "local",
                    "source": "local",
                    "type": "local",
                    "file": f"local-plugins/{tag.slug}.zip",
                })
        else:
            entry = lock_entries.get(tag.slug)
            plugins.append({
                "name": tag.slug,
                "version": entry.version if entry else "?",
                "source": tag.source,
                "type": "store",
            })

    manifest = {
        "version": 1,
        "exported_at": datetime.now(UTC).isoformat(),
        "project": {
            "name": config.name,
            "godot": config.godot,
        },
        "plugins": plugins,
    }

    # Create zip
    if not output:
        output_dir = root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        output = str(output_dir / f"{config.name}-{date_str}.zip")

    output_path = Path(output)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write manifest
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )

        # Add local plugin zips
        for name in local_files:
            local_zip = local_dir / f"{name}.zip"
            zf.write(local_zip, f"local-plugins/{name}.zip")

    console.print(f"[green]✓[/green] Exported to [cyan]{output_path}[/cyan]")
    console.print(f"  {len(plugins)} plugin(s)")
    if local_files:
        console.print(f"  {len(local_files)} local plugin(s)")
