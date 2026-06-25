"""CLI application entry point."""

from __future__ import annotations

from typing import Any

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gdpm import __tag__, __version__
from gdpm.constants import GITHUB_API_URL, REPO_URL

console = Console()

BANNER = r""" ██████╗ ██████╗ ██████╗ ███╗   ███╗
██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
██║  ███╗██║  ██║██████╔╝██╔████╔██║
██║   ██║██║  ██║██╔═══╝ ██║╚██╔╝██║
╚██████╔╝██████╔╝██║     ██║ ╚═╝ ██║
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝     ╚═╝"""

COMMANDS = {
    "Project": {
        "init": "Initialize a new gdpm project",
        "sync": "Sync addons/ to lock file state",
        "lock": "Generate or update lock file",
        "list": "List installed plugins",
        "status": "Show plugin status and updates",
    },
    "Dependencies": {
        "add": "Add plugins to the project",
        "remove": "Remove plugins",
        "update": "Update plugins to newer versions",
        "search": "Search Godot Asset Store",
        "info": "Show plugin details",
        "cache": "Manage global cache (info, clean)",
    },
    "Import/Export": {
        "export": "Export plugins to zip archive",
        "import": "Import plugins from zip archive",
    },
}


class GdpmCommand(click.Command):
    """Custom command class with Rich-formatted help."""

    def __init__(
        self,
        *args: Any,
        examples: list[tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.examples: list[tuple[str, str]] = examples or []

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        console.print()
        console.print(
            Text(f"  gdpm {ctx.info_name}", style="bold green")
            + Text(f"  {self.help or ''}", style="dim")
        )
        console.print()

        usage_parts = [f"gdpm {ctx.info_name}"]
        for param in self.params:
            if param.name == "help":
                continue
            if param.required:
                usage_parts.append(f"<{param.name}>")
            elif isinstance(param, click.Option) and param.is_flag:
                usage_parts.append(f"[--{param.name}]")
            else:
                usage_parts.append(f"[--{param.name} VALUE]")
        console.print(
            Text("  Usage: ", style="dim") + Text(" ".join(usage_parts), style="white")
        )
        console.print()

        options = [
            p for p in self.params if p.name != "help" and isinstance(p, click.Option)
        ]
        if options:
            table = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style="bold",
                padding=(0, 2),
                width=min(80, 90),
            )
            table.add_column("Option", style="green", min_width=20, justify="left")
            table.add_column("Description", justify="left")

            for param in options:
                opts = ", ".join(param.opts)
                desc = param.help or ""
                default = ""
                if param.default is not None and not param.is_flag:
                    default = f" [dim](default: {param.default})[/dim]"
                elif param.is_flag and param.default:
                    default = " [dim](default: on)[/dim]"
                table.add_row(f"  {opts}", f"{desc}{default}")

            console.print(
                Panel(
                    table,
                    title="[bold cyan]Options[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                    width=min(80, 90),
                )
            )

        if self.examples:
            lines = []
            for example_cmd, example_desc in self.examples:
                lines.append(f"  [dim]# {example_desc}[/dim]")
                lines.append(f"  $ {example_cmd}")
            console.print(
                Panel(
                    "\n".join(lines),
                    title="[bold cyan]Examples[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                    width=min(80, 90),
                )
            )


class GdpmGroup(click.Group):
    """Custom group class with Rich-formatted help."""

    def __init__(
        self,
        *args: Any,
        examples: list[tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.examples: list[tuple[str, str]] = examples or []

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        terminal_width = console.width
        panel_width = min(terminal_width - 6, 80)

        if ctx.info_name == "gdpm":
            self._format_main_help(ctx, panel_width)
        else:
            self._format_group_help(ctx, panel_width)

    def _format_main_help(self, ctx: click.Context, panel_width: int) -> None:
        console.print()

        for category, cmds in COMMANDS.items():
            table = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style="bold magenta",
                padding=(0, 2),
                width=panel_width - 4,
            )
            table.add_column("Command", style="green", width=16, justify="left")
            table.add_column("Description", justify="left")

            for cmd_name, desc in cmds.items():
                table.add_row(f"  {cmd_name}", desc)

            console.print(
                Panel(
                    table,
                    title=f"[bold cyan]{category}[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                    width=panel_width,
                )
            )

        console.print()
        console.print(
            Text("  Usage: ", style="dim")
            + Text("gdpm", style="bold green")
            + Text(" <command>", style="white")
            + Text(" [options]", style="dim")
        )
        console.print(
            Text("  Help:  ", style="dim")
            + Text("gdpm", style="bold green")
            + Text(" <command>", style="white")
            + Text(" --help", style="dim")
        )
        console.print()
        console.print(
            Panel(
                Text("  -h, --help      Show help message\n", style="dim")
                + Text("  -i, --info      Show project info and version\n", style="dim")
                + Text("  -V, --version   Show version\n", style="dim")
                + Text("  -y, --yes       Skip confirmation prompts", style="dim"),
                title="[bold cyan]Common Options[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=panel_width,
            )
        )

    def _format_group_help(self, ctx: click.Context, panel_width: int) -> None:
        console.print()
        console.print(
            Text(f"  gdpm {ctx.info_name}", style="bold green")
            + Text(f"  {self.help or ''}", style="dim")
        )
        console.print()
        console.print(
            Text("  Usage: ", style="dim")
            + Text(f"gdpm {ctx.info_name}", style="bold green")
            + Text(" <command>", style="white")
        )
        console.print()

        table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold magenta",
            padding=(0, 2),
            width=panel_width - 4,
        )
        table.add_column("Command", style="green", width=16, justify="left")
        table.add_column("Description", justify="left")

        for name, cmd in self.commands.items():
            table.add_row(f"  {name}", cmd.help or "")

        console.print(
            Panel(
                table,
                title="[bold cyan]Commands[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=panel_width,
            )
        )

        if self.examples:
            lines = []
            for example_cmd, example_desc in self.examples:
                lines.append(f"  [dim]# {example_desc}[/dim]")
                lines.append(f"  $ {example_cmd}")
            console.print(
                Panel(
                    "\n".join(lines),
                    title="[bold cyan]Examples[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                    width=panel_width,
                )
            )


def print_info(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    """Print project info with banner and version."""
    if not value:
        return

    import re

    import httpx

    from gdpm.utils.install import get_install_type, get_platform

    base_version = re.sub(r"(\.dev\d+|[a-z]\d+|rc\d+)$", "", __version__)
    tag_display = f" [{__tag__}]" if __tag__ else ""
    install_type = get_install_type()
    platform_info = get_platform()

    from rich.console import Group

    info_lines = []
    info_lines.append(Text(BANNER, style="bold cyan"))
    info_lines.append(Text(""))
    info_lines.append(
        Text("  gdpm", style="bold white")
        + Text(f" v{base_version}", style="yellow")
        + Text(tag_display, style="dim")
    )
    info_lines.append(Text("  Godot Dependency Package Manager", style="dim"))
    info_lines.append(Text(f"  Install: {install_type}", style="dim"))
    info_lines.append(Text(f"  Platform: {platform_info}", style="dim"))
    info_lines.append(Text(""))
    info_lines.append(
        Text("  GitHub: ", style="dim")
        + Text(REPO_URL, style="blue underline")
    )

    terminal_width = console.width
    console.print()
    console.print(
        Panel(
            Group(*info_lines),
            title="[bold cyan]GDPM-Info[/bold cyan]",
            border_style="dim",
            padding=(1, 2),
            width=min(terminal_width, 90),
        )
    )

    try:
        resp = httpx.get(f"{GITHUB_API_URL}contributors", timeout=5, verify=False)
        if resp.status_code == 200:
            contributors = sorted(
                [c["login"] for c in resp.json()],
                key=str.lower,
            )
            contrib_text = Text()
            for i, name in enumerate(contributors):
                if i > 0:
                    contrib_text.append("  ")
                contrib_text.append(f"@{name}", style="cyan")
            console.print()
            console.print(
                Panel(
                    contrib_text,
                    title="[bold cyan]Contributors[/bold cyan]",
                    border_style="dim",
                    padding=(1, 2),
                width=min(terminal_width, 90),
                )
            )
    except Exception:
        pass

    console.print()
    ctx.exit()


def print_version(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    """Print version info."""
    if not value:
        return

    import re

    base_version = re.sub(r"(\.dev\d+|[a-z]\d+|rc\d+)$", "", __version__)
    tag_display = f"[{__tag__}]" if __tag__ else ""

    if tag_display:
        console.print(
            Text("gdpm", style="bold white")
            + Text(f" v{base_version}", style="yellow")
            + Text(f" {tag_display}", style="dim")
        )
    else:
        console.print(
            Text("gdpm", style="bold white")
            + Text(f" v{base_version}", style="yellow")
        )
    ctx.exit()


@click.group(cls=GdpmGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-i",
    "--info",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=print_info,
    help="Show project info and version.",
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=print_version,
    help="Show version and exit.",
)
def main() -> None:
    """Godot Dependency Package Manager."""


from gdpm.cli.add import add as add_cmd  # noqa: E402
from gdpm.cli.cache_cmd import cache as cache_cmd  # noqa: E402
from gdpm.cli.export import export as export_cmd  # noqa: E402
from gdpm.cli.import_cmd import import_cmd as import_cmd_  # noqa: E402
from gdpm.cli.info import info as info_cmd  # noqa: E402
from gdpm.cli.init import init as init_cmd  # noqa: E402
from gdpm.cli.list import list_cmd  # noqa: E402
from gdpm.cli.lock import lock as lock_cmd  # noqa: E402
from gdpm.cli.remove import remove as remove_cmd  # noqa: E402
from gdpm.cli.search import search as search_cmd  # noqa: E402
from gdpm.cli.status import status as status_cmd  # noqa: E402
from gdpm.cli.sync import sync as sync_cmd  # noqa: E402
from gdpm.cli.update import update as update_cmd  # noqa: E402

main.add_command(add_cmd, "add")  # type: ignore[has-type]
main.add_command(cache_cmd, "cache")
main.add_command(export_cmd, "export")
main.add_command(import_cmd_, "import")
main.add_command(info_cmd, "info")
main.add_command(init_cmd, "init")
main.add_command(list_cmd, "list")
main.add_command(lock_cmd, "lock")
main.add_command(remove_cmd, "remove")
main.add_command(search_cmd, "search")
main.add_command(status_cmd, "status")
main.add_command(sync_cmd, "sync")
main.add_command(update_cmd, "update")
