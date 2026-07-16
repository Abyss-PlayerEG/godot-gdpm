"""gdpm godot list command."""

from __future__ import annotations

import re

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.godot.common import get_engines_dir
from gdpm.constants import GODOT_RELEASES_URL, get_github_headers


def _list_local(show_id: bool = False) -> None:
    """List installed Godot versions."""
    from gdpm.config.local_engines import load_local_engines
    from gdpm.utils.path import shorten_path

    engines_dir = get_engines_dir()
    local_engines = load_local_engines()

    rows: list[dict[str, str]] = []

    if engines_dir.exists():
        for d in sorted(engines_dir.iterdir()):
            if d.is_dir():
                rows.append(
                    {
                        "name": "gdpm-godot",
                        "version": d.name,
                        "source": shorten_path(str(d)),
                    }
                )

    for name, engine in sorted(local_engines.items()):
        rows.append(
            {
                "name": name,
                "version": engine.version or "-",
                "source": shorten_path(engine.path),
            }
        )

    if not rows:
        console.print(
            "[dim]No Godot versions installed.[/dim]\n"
            "  Use [bold]gdpm godot install <version>[/bold] to install.\n"
            "  Use [bold]gdpm godot add <path>[/bold] to add a local engine."
        )
        return

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )

    if show_id:
        table.add_column("ID", style="yellow", min_width=25)
        table.add_column("Source", style="dim")
        for row in rows:
            engine_id = f"{row['name']}@{row['version']}"
            table.add_row(engine_id, row["source"])
    else:
        table.add_column("Name", style="cyan", min_width=15)
        table.add_column("Version", style="green", min_width=15)
        table.add_column("Source", style="dim")
        for row in rows:
            table.add_row(row["name"], row["version"], row["source"])

    console.print(
        Panel(
            table,
            title=f"[bold cyan]Installed Godot ({len(rows)})[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )


def _list_remote(version_filter: str, show_all: bool, page: int = 1) -> None:
    """List available Godot versions from GitHub."""
    try:
        if version_filter:
            releases = []
            current_page = 1
            while True:
                resp = httpx.get(
                    GODOT_RELEASES_URL,
                    params={"per_page": 100, "page": current_page},
                    headers=get_github_headers(),
                    timeout=10,
                    verify=False,
                )
                resp.raise_for_status()
                page_data = resp.json()
                if not page_data:
                    break
                releases.extend(page_data)

                link_header = resp.headers.get("link", "")
                if 'rel="next"' not in link_header:
                    break
                current_page += 1

            total_pages = 1
        else:
            resp1 = httpx.get(
                GODOT_RELEASES_URL,
                params={"per_page": 30, "page": 1},
                headers=get_github_headers(),
                timeout=10,
                verify=False,
            )
            resp1.raise_for_status()
            total_pages = 1
            link1 = resp1.headers.get("link", "")
            match = re.search(r"page=(\d+)>; rel=\"last\"", link1)
            if match:
                total_pages = int(match.group(1))

            if page == 1:
                releases = resp1.json()
            else:
                resp = httpx.get(
                    GODOT_RELEASES_URL,
                    params={"per_page": 30, "page": page},
                    headers=get_github_headers(),
                    timeout=10,
                    verify=False,
                )
                resp.raise_for_status()
                releases = resp.json()
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to fetch releases: {e}")
        return

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )
    table.add_column("Version", style="cyan", min_width=20)
    table.add_column("Type", min_width=10)
    table.add_column("Date", min_width=12)

    for r in releases:
        tag = r.get("tag_name", "")
        pre = r.get("prerelease", False)
        date = r.get("published_at", "")[:10]

        if version_filter:
            if not tag.startswith(version_filter):
                continue
        elif not show_all and not tag.startswith(("3.", "4.", "5.")):
            continue

        ver_type = "[yellow]Pre-release[/yellow]" if pre else "[green]Stable[/green]"
        table.add_row(tag, ver_type, date)

    if not table.row_count:
        console.print(
            "[dim]No versions on this page. "
            "Use [bold]-a[/bold] to show all versions.[/dim]"
        )
        return

    console.print(
        Panel(
            table,
            title=(
                f"[bold cyan]Available Godot Versions "
                f"(page {page}/{total_pages})[/bold cyan]"
            ),
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )


@click.command(
    name="list",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot list", "List installed versions"),
        ("gdpm godot list --remote", "List available versions"),
    ],
)
@click.option(
    "--remote", "-r", is_flag=True, help="List available versions from GitHub"
)
@click.option(
    "-V",
    "--version",
    "version_filter",
    default="",
    metavar="VERSION",
    help="Filter by version (e.g. '4.7', '3.6')",
)
@click.option(
    "-a",
    "--all",
    "show_all",
    is_flag=True,
    help="Show all versions including 1.x/2.x",
)
@click.option(
    "-p", "--page", "page", default=1, type=int, help="Page number for remote list"
)
@click.option(
    "-id", "show_id", is_flag=True, help="Show ID column instead of Name and Version"
)
def godot_list(
    remote: bool, version_filter: str, show_all: bool, page: int, show_id: bool
) -> None:
    """List Godot engine versions."""
    if remote:
        _list_remote(version_filter, show_all, page)
    else:
        _list_local(show_id)
