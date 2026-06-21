"""gdpm search command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console

from gdpm.cli.common import is_template, require_project
from gdpm.config.project import read_project_config
from gdpm.store.client import StoreClient
from gdpm.utils.version import is_compatible

console = Console()


@click.command()
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Number of results")
@click.option(
    "--sort",
    type=click.Choice([
        "relevance", "updated_desc", "reviews_desc", "created_desc",
    ]),
    default="relevance",
    help="Sort order",
)
@click.option("--all", "show_all", is_flag=True, help="Include project templates")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search(
    query: str, limit: int, sort: str, show_all: bool, as_json: bool
) -> None:
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
            click.echo(json.dumps(output, indent=2))
            return

        console.print(
            f"Search results for [bold]{query}[/bold] "
            f"({len(results)} found):\n"
        )

        for plugin in results:
            add_route = f"{plugin.publisher_slug}/{plugin.slug}"

            if is_template(plugin.tags):
                console.print(
                    f"  [bold yellow]{plugin.name}[/bold yellow] "
                    "[dim](template)[/dim]"
                )
            else:
                console.print(f"  [bold cyan]{plugin.name}[/bold cyan]")

            desc = plugin.description[:100]
            if len(plugin.description) > 100:
                desc += "..."
            console.print(f"    {desc}")

            tags = ", ".join(plugin.tags) if plugin.tags else ""
            meta_parts = []
            if plugin.license:
                meta_parts.append(f"License: {plugin.license}")
            if plugin.stars:
                meta_parts.append(f"Score: {plugin.stars}")
            meta = "  |  ".join(meta_parts)
            if meta:
                console.print(f"    [dim]{meta}[/dim]")

            if not is_template(plugin.tags):
                try:
                    versions = await client.get_versions(
                        plugin.publisher_slug, plugin.slug
                    )
                    if versions:
                        latest = versions[0]
                        ver = latest.get("version", "")
                        min_godot = latest.get("min_godot_version", "")
                        max_godot = latest.get("max_godot_version", "")

                        ver_display = (
                            ver if ver.startswith(("v", "V"))
                            else f"v{ver}"
                        )
                        console.print(f"    [dim]{ver_display}[/dim]")

                        godot_parts = []
                        if min_godot and min_godot not in ("None", ""):
                            godot_parts.append(f">={min_godot}")
                        if max_godot and max_godot not in ("None", ""):
                            godot_parts.append(f"<={max_godot}")

                        if godot_parts:
                            console.print(
                                f"    [dim]Godot "
                                f"{' '.join(godot_parts)}[/dim]"
                            )

                        if project_godot:
                            compatible, msg = is_compatible(
                                project_godot, min_godot, max_godot
                            )
                            if compatible:
                                console.print(
                                    "    [green]✓ Compatible[/green]"
                                )
                            else:
                                console.print(
                                    f"    [red]✗ {msg}[/red]"
                                )
                except Exception:
                    pass

            if tags:
                console.print(f"    [dim]Tags: {tags}[/dim]")

            if plugin.store_url:
                console.print(
                    f"    [dim]{plugin.store_url}[/dim]"
                )

            if is_template(plugin.tags):
                console.print(
                    "    [dim]Project template - "
                    "not installable as addon[/dim]"
                )
            else:
                console.print(
                    f"    [green]gdpm add {add_route}[/green]"
                )
            console.print()

    asyncio.run(_search())
