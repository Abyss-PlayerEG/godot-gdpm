"""gdpm search command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console

from gdpm.store.client import StoreClient

console = Console()


@click.command()
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Number of results")
@click.option(
    "--sort",
    type=click.Choice(["relevance", "updated_desc", "reviews_desc", "created_desc"]),
    default="relevance",
    help="Sort order",
)
@click.option("--all", "show_all", is_flag=True, help="Include project templates")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search(query: str, limit: int, sort: str, show_all: bool, as_json: bool) -> None:
    """Search for plugins in the Godot Asset Store."""

    async def _search() -> None:
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
            f"Search results for [bold]{query}[/bold] ({len(results)} found):\n"
        )

        for plugin in results:
            add_route = f"{plugin.publisher_slug}/{plugin.slug}"

            template_tags = {"template", "starterkit", "demo", "project"}
            is_template = any(t.lower() in template_tags for t in plugin.tags)

            if is_template:
                console.print(
                    f"  [bold yellow]{plugin.name}[/bold yellow] [dim](template)[/dim]"
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
            if tags:
                console.print(f"    [dim]Tags: {tags}[/dim]")
            if is_template:
                console.print(
                    "    [dim]Project template - not installable as addon[/dim]"
                )
            else:
                console.print(f"    [green]gdpm add {add_route}[/green]")
            console.print()

    asyncio.run(_search())
