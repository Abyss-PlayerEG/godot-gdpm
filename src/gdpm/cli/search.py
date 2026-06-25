"""gdpm search command."""

from __future__ import annotations

import asyncio

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, is_template, require_project
from gdpm.cli.display import display_plugin_meta, display_version_info
from gdpm.config.project import read_project_config
from gdpm.store.client import StoreClient


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm search mcp", "Search for MCP plugins"),
        ("gdpm search ai --limit 5", "Show top 5 results"),
        ("gdpm search controller --all", "Include templates"),
        ("gdpm search input --sort downloads", "Sort by downloads"),
    ],
)
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Number of results")
@click.option(
    "--sort",
    type=click.Choice(
        ["relevance", "updated_desc", "reviews_desc", "created_desc"],
    ),
    default="relevance",
    help="Sort order: relevance, updated_desc, reviews_desc, created_desc",
)
@click.option("--all", "show_all", is_flag=True, help="Include project templates")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search(query: str, limit: int, sort: str, show_all: bool, as_json: bool) -> None:
    """Search for plugins in the Godot Asset Store."""

    async def _search() -> None:
        try:
            root = require_project()
            config = read_project_config(root / "gdproject.toml")
            project_godot = config.godot
        except Exception:
            project_godot = ""

        client = StoreClient()
        try:
            results = await client.search(
                query, limit=limit, sort=sort, include_projects=show_all
            )
        finally:
            await client.close()

        # Filter out templates unless --all is used
        if not show_all:
            results = [r for r in results if not is_template(r.tags)]

        if not results:
            console.print(f"No results found for [bold]{query}[/bold]")
            return

        if as_json:
            import json

            output = [
                {
                    "slug": p.slug,
                    "name": p.name,
                    "description": p.description,
                    "author": p.author,
                    "license": p.license,
                    "tags": p.tags,
                    "stars": p.stars,
                }
                for p in results
            ]
            console.print(json.dumps(output, indent=2))
            return

        console.print(
            f"Search results for [bold]{query}[/bold] ({len(results)} found):\n"
        )

        for plugin in results:
            add_route = f"{plugin.publisher_slug}/{plugin.slug}"
            console.print(f"  [bold cyan]{plugin.name}[/bold cyan]")

            desc = plugin.description[:100]
            if len(plugin.description) > 100:
                desc += "..."
            console.print(f"    {desc}")

            display_plugin_meta(
                license_name=plugin.license,
                stars=plugin.stars,
                tags=plugin.tags,
                store_url=plugin.store_url,
            )

            if not is_template(plugin.tags):
                try:
                    versions = await client.get_versions(
                        plugin.publisher_slug, plugin.slug
                    )
                    if versions:
                        latest = versions[0]
                        display_version_info(
                            ver=latest.get("version", ""),
                            min_godot=latest.get("min_godot_version", ""),
                            max_godot=latest.get("max_godot_version", ""),
                            project_godot=project_godot,
                        )
                except Exception:
                    pass

            if is_template(plugin.tags):
                console.print(
                    "    [dim]Project template - not installable as addon[/dim]"
                )
            else:
                console.print(f"    [green]gdpm add {add_route}[/green]")

    asyncio.run(_search())
