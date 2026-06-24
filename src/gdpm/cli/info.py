"""gdpm info command."""

from __future__ import annotations

import asyncio

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
                    console.print(
                        f"[red]Error:[/red] Plugin '{slug}' not found."
                    )
                    raise SystemExit(1)

                exact = next(
                    (r for r in results if r.slug == slug), None
                )
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

        # Header
        console.print()
        console.print(
            Text(f"  {detail.name}", style="bold cyan")
            + Text(f"  {detail.latest_version}", style="dim")
        )
        console.print()

        # Description
        console.print(
            Panel(
                f"  {detail.description}",
                border_style="dim",
                padding=(1, 2),
            )
        )

        # Info table
        info_table = Table(
            box=box.SIMPLE,
            show_header=False,
            padding=(0, 2),
        )
        info_table.add_column("Key", style="bold", min_width=12)
        info_table.add_column("Value")

        if detail.author:
            info_table.add_row("Author", detail.author)
        if detail.license:
            info_table.add_row("License", detail.license)
        if detail.tags:
            info_table.add_row("Tags", ", ".join(detail.tags))
        if detail.homepage:
            info_table.add_row(
                "Store",
                f"[link={detail.homepage}]{detail.homepage}[/link]",
            )

        console.print(
            Panel(
                info_table,
                title="[bold cyan]Info[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
            )
        )

        # Install command
        if is_template(detail.tags):
            console.print(
                Panel(
                    "  [yellow]Project template - "
                    "not installable as addon[/yellow]",
                    border_style="dim",
                    padding=(0, 1),
                )
            )
        else:
            console.print(
                Panel(
                    f"  [green]gdpm add {add_route}[/green]",
                    title="[bold cyan]Install[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                )
            )

        # Versions
        if versions:
            ver_table = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style="bold",
                padding=(0, 2),
            )
            ver_table.add_column(
                "Version", style="cyan", min_width=15, justify="left"
            )
            ver_table.add_column("Date", justify="left")
            ver_table.add_column("Type", justify="left")

            for v in versions[:10]:
                ver = v.get("version", "")
                stable = "stable" if v.get("stable") == "True" else "pre"
                date = v.get("created", "")
                ver_table.add_row(ver, date, stable)

            console.print()
            console.print(
                Panel(
                    ver_table,
                    title="[bold cyan]Versions[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                )
            )

        console.print()

    asyncio.run(_info())
