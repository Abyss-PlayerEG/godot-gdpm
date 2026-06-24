"""CLI application entry point."""

from __future__ import annotations

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gdpm import __tag__, __version__

console = Console()

BANNER = r"""
 ██████╗ ██████╗ ██████╗ ███╗   ███╗
██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
██║  ███╗██║  ██║██████╔╝██╔████╔██║
██║   ██║██║  ██║██╔═══╝ ██║╚██╔╝██║
╚██████╔╝██████╔╝██║     ██║ ╚═╝ ██║
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝     ╚═╝
"""

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
    },
    "Import/Export": {
        "export": "Export plugins to zip archive",
        "import": "Import plugins from zip archive",
    },
}


class GdpmGroup(click.Group):
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        banner_text = Text(BANNER, style="bold cyan")
        version_text = Text(f"  v{__version__}", style="dim")

        console.print(banner_text)
        console.print(version_text)
        console.print()

        console.print(
            Text("  [DEV] ", style="bold yellow")
            + Text("This project is under active development.", style="dim")
        )
        console.print(
            Text("  Report issues: ", style="dim")
            + Text("https://github.com/Abyss-PlayerEG/godot-gdpm/issues", style="blue")
        )
        console.print()

        console.print(Text("  Godot Dependency Package Manager", style="bold white"))
        console.print(
            Text("  https://github.com/Abyss-PlayerEG/godot-gdpm", style="dim")
        )
        console.print()

        terminal_width = console.width

        for category, cmds in COMMANDS.items():
            table = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style="bold magenta",
                padding=(0, 2),
                width=terminal_width - 6,
            )
            table.add_column("Command", style="green", min_width=12)
            table.add_column("Description")

            for cmd_name, desc in cmds.items():
                table.add_row(f"  {cmd_name}", desc)

            console.print(
                Panel(
                    table,
                    title=f"[bold cyan]{category}[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                    width=terminal_width,
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

        # Common options
        console.print(
            Panel(
                Text("  -h, --help     Show help message\n", style="dim")
                + Text("  -V, --version  Show version\n", style="dim")
                + Text("  -y, --yes      Skip confirmation prompts", style="dim"),
                title="[bold cyan]Common Options[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=terminal_width,
            )
        )
        console.print()


def print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Print formatted version info."""
    if not value:
        return

    import re

    # Extract base version (remove tag suffix like b1, dev1, a1, rc1)
    base_version = re.sub(r"(\.dev\d+|[a-z]\d+|rc\d+)$", "", __version__)
    tag_display = f" [{__tag__}]" if __tag__ else ""

    console.print()
    console.print(Text(BANNER, style="bold cyan"))
    console.print()
    console.print(
        Text("  gdpm", style="bold white")
        + Text(f" v{base_version}", style="bold green")
        + Text(tag_display, style="bold yellow")
    )
    console.print(Text("  Godot Dependency Package Manager", style="dim"))
    console.print()
    console.print(
        Text("  Report issues: ", style="dim")
        + Text(
            "https://github.com/Abyss-PlayerEG/godot-gdpm/issues",
            style="blue underline",
        )
    )
    console.print()
    ctx.exit()


@click.group(cls=GdpmGroup, context_settings={"help_option_names": ["-h", "--help"]})
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


from gdpm.cli.add import add  # noqa: E402
from gdpm.cli.export import export  # noqa: E402
from gdpm.cli.import_cmd import import_cmd  # noqa: E402
from gdpm.cli.info import info  # noqa: E402
from gdpm.cli.init import init  # noqa: E402
from gdpm.cli.list import list_cmd  # noqa: E402
from gdpm.cli.lock import lock  # noqa: E402
from gdpm.cli.remove import remove  # noqa: E402
from gdpm.cli.search import search  # noqa: E402
from gdpm.cli.status import status  # noqa: E402
from gdpm.cli.sync import sync  # noqa: E402
from gdpm.cli.update import update  # noqa: E402

main.add_command(add)
main.add_command(export)
main.add_command(import_cmd, "import")
main.add_command(info)
main.add_command(init)
main.add_command(list_cmd, "list")
main.add_command(lock)
main.add_command(remove)
main.add_command(search)
main.add_command(status)
main.add_command(sync)
main.add_command(update)
