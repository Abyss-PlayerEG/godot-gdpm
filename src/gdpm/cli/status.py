"""gdpm status command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.table import Table

from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.store.client import StoreClient
from gdpm.utils.version import normalize_version

console = Console()

TAG_FILENAME = "tag.gdpm"


@click.command()
@click.argument("plugin_slug", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(plugin_slug: str | None, as_json: bool) -> None:
    """Show plugin status and available updates."""

    async def _status() -> None:
        root = require_project()
        config_path = root / "gdproject.toml"
        config = read_project_config(config_path)
        addons_dir = root / config.addons_dir
        lock_path = find_lockfile(root)

        lock_entries = read_lockfile(lock_path)
        lock_map = {e.name: e for e in lock_entries}

        installed: list[dict[str, str]] = []

        if addons_dir.exists():
            for child in sorted(addons_dir.iterdir()):
                if not child.is_dir():
                    continue

                tag_path = child / TAG_FILENAME
                if not tag_path.exists():
                    continue

                tag_content = tag_path.read_text(encoding="utf-8").strip()

                slug = ""
                if "/" in tag_content:
                    slug = tag_content.split("/")[-1]
                else:
                    slug = tag_content.split("+")[-1]

                if plugin_slug and slug != plugin_slug:
                    continue

                locked = lock_map.get(slug)
                version = locked.version if locked else "?"

                installed.append(
                    {
                        "slug": slug,
                        "dir_name": child.name,
                        "version": version,
                        "source": tag_content,
                    }
                )

        if not installed:
            if plugin_slug:
                console.print(f"[red]Plugin '{plugin_slug}' not installed.[/red]")
            else:
                console.print("[dim]No plugins installed.[/dim]")
            return

        store = StoreClient()
        results: list[dict[str, str]] = []

        try:
            for plugin in installed:
                slug = plugin["slug"]
                current_ver = plugin["version"]

                source = plugin["source"]
                publisher = ""
                if "/" in source:
                    clean_source = source.replace("store+", "")
                    parts = clean_source.split("/")
                    if len(parts) >= 2:
                        publisher = parts[0]

                latest_ver = current_ver
                if publisher:
                    try:
                        versions = await store.get_versions(publisher, slug)
                        if versions:
                            latest_ver = versions[0].get("version", current_ver)
                    except Exception as e:
                        console.print(
                            f"  [dim]Failed to fetch versions for {slug}: {e}[/dim]"
                        )

                current_norm = normalize_version(current_ver.lstrip("vV"))
                latest_norm = normalize_version(latest_ver.lstrip("vV"))

                if current_norm == latest_norm:
                    update_status = "✓ Up to date"
                else:
                    update_status = f"⬆ {latest_ver}"

                results.append(
                    {
                        "slug": slug,
                        "version": current_ver,
                        "latest": latest_ver,
                        "status": update_status,
                        "dir_name": plugin["dir_name"],
                    }
                )
        finally:
            await store.close()

        if as_json:
            import json

            click.echo(json.dumps(results, indent=2))
            return

        console.print(f"[bold]Plugin status ({len(results)}):[/bold]\n")

        table = Table(show_header=True, header_style="bold", box=None)
        table.add_column("Plugin", style="cyan", min_width=20)
        table.add_column("Version", min_width=10)
        table.add_column("Latest", min_width=10)
        table.add_column("Status", min_width=15)

        for r in results:
            status_style = "green" if "Up to date" in r["status"] else "yellow"
            table.add_row(
                r["slug"],
                r["version"],
                r["latest"],
                f"[{status_style}]{r['status']}[/{status_style}]",
            )

        console.print(table)

        updates = [r for r in results if "⬆" in r["status"]]
        if updates:
            console.print(
                f"\n[yellow]{len(updates)} update(s) available. "
                f"Run 'gdpm update' to update.[/yellow]"
            )

        console.print()

    asyncio.run(_status())
