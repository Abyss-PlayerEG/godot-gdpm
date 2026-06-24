"""gdpm info command."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.panel import Panel

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import is_template
from gdpm.store.client import StoreClient

console = Console()


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm info limbo-ai", "Show plugin details"),
        ("gdpm info rsubtil/controller-icons", "Show with publisher/slug"),
    ],
)
@click.argument("plugin_slug")
def info(plugin_slug: str) -> None:
    """Show detailed information about a plugin."""

    parts = plugin_slug.split("/")
    if len(parts) == 2:
        publisher, slug = parts
    else:
        publisher = ""
        slug = plugin_slug

    async def _info() -> None:
        client = StoreClient()

        try:
            if not publisher:
                results = await client.search(slug, limit=20)
                if not results:
                    console.print(f"[red]Error:[/red] Plugin '{slug}' not found.")
                    raise SystemExit(1)

                exact = next((r for r in results if r.slug == slug), None)
                if exact:
                    author = exact.publisher_slug
                else:
                    console.print(
                        f"[red]Error:[/red] Plugin '{slug}' not found. "
                        f"Did you mean: {results[0].slug}?"
                    )
                    raise SystemExit(1)
            else:
                author = publisher

            detail = await client.get_plugin(author, slug)
            versions = await client.get_versions(author, slug)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1) from e
        finally:
            await client.close()

        add_route = f"{author}/{slug}"

        # Build info content
        info_lines = []
        info_lines.append(
            f"[bold cyan]{detail.name}[/bold cyan]"
            + (f"  [dim]{detail.latest_version}[/dim]" if detail.latest_version else "")
        )
        info_lines.append("")
        info_lines.append(detail.description)
        info_lines.append("")

        if detail.author:
            info_lines.append(f"  Author:     {detail.author}")
        if detail.license:
            info_lines.append(f"  License:    {detail.license}")
        if detail.homepage:
            info_lines.append(f"  Store:      {detail.homepage}")
        if detail.tags:
            info_lines.append(f"  Tags:       {', '.join(detail.tags)}")
        info_lines.append("")

        if is_template(detail.tags):
            info_lines.append(
                "  [yellow]Project template - not installable as addon[/yellow]"
            )
        else:
            info_lines.append(f"  Install:    [green]gdpm add {add_route}[/green]")

        # Add versions table if available
        if versions:
            info_lines.append("")
            info_lines.append("  [bold]Versions:[/bold]")
            for v in versions[:10]:
                ver = v.get("version", "")
                stable = "stable" if v.get("stable") == "True" else "pre"
                date = v.get("created", "")
                info_lines.append(f"    {ver}  {date}  [{stable}]")

        console.print()
        console.print(
            Panel(
                "\n".join(info_lines),
                title="[bold cyan]Info[/bold cyan]",
                border_style="dim",
                padding=(1, 2),
                width=120,
            )
        )
        console.print()

    asyncio.run(_info())
