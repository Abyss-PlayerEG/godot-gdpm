"""gdpm status command."""

from __future__ import annotations

import asyncio

import click
from rich.table import Table

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.context import get_project_context
from gdpm.store.client import StoreClient
from gdpm.utils.tag import scan_addons
from gdpm.utils.version import normalize_version


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm status", "Show status of all plugins"),
        ("gdpm status limbo-ai", "Show status of specific plugin"),
        ("gdpm status --json", "Output as JSON"),
    ],
)
@click.argument("plugin_slug", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(plugin_slug: str | None, as_json: bool) -> None:
    """Show plugin status and available updates."""

    async def _status() -> None:
        ctx = get_project_context()

        installed: list[dict[str, str]] = []

        for _, tag in scan_addons(ctx.addons_dir):
            if plugin_slug and tag.slug != plugin_slug:
                continue

            locked = ctx.lock_map.get(tag.slug)
            version = "local" if tag.is_local else (locked.version if locked else "?")

            installed.append(
                {
                    "slug": tag.slug,
                    "version": version,
                    "source": tag.source,
                    "is_local": str(tag.is_local),
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
            version_map: dict[str, str] = {}
            with console.status("Loading...", spinner="dots"):
                for plugin in installed:
                    slug = plugin["slug"]
                    is_local = plugin.get("is_local", "False") == "True"

                    if is_local:
                        continue

                    source = plugin["source"]
                    publisher = ""
                    if "/" in source:
                        clean = source.replace("store+", "")
                        parts = clean.split("/")
                        if len(parts) >= 2:
                            publisher = parts[0]

                    if publisher:
                        try:
                            versions = await store.get_versions(publisher, slug)
                            if versions:
                                version_map[slug] = versions[0].get("version", "")
                        except Exception:
                            pass

            for plugin in installed:
                slug = plugin["slug"]
                current_ver = plugin["version"]
                is_local = plugin.get("is_local", "False") == "True"

                if is_local:
                    results.append(
                        {
                            "slug": slug,
                            "version": "local",
                            "latest": "local",
                            "status": "✓ Local",
                        }
                    )
                    continue

                latest_ver = version_map.get(slug, current_ver)

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
                    }
                )
        finally:
            await store.close()

        if as_json:
            import json

            console.print(json.dumps(results, indent=2))
            return

        console.print(f"[bold]Plugin status ({len(results)}):[/bold]\n")

        table = Table(show_header=True, header_style="bold", box=None)
        table.add_column("Plugin", style="cyan", min_width=20)
        table.add_column("Version", min_width=10)
        table.add_column("Latest", min_width=10)
        table.add_column("Status", min_width=15)

        for r in results:
            style = "green" if "Up to date" in r["status"] else "yellow"
            table.add_row(
                r["slug"],
                r["version"],
                r["latest"],
                f"[{style}]{r['status']}[/{style}]",
            )

        console.print(table)

        updates = [r for r in results if "⬆" in r["status"]]
        if updates:
            console.print(
                f"\n[yellow]{len(updates)} update(s) available. "
                f"Run 'gdpm update' to update.[/yellow]"
            )

    asyncio.run(_status())
