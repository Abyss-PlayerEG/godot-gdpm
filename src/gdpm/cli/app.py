"""CLI application entry point."""

from __future__ import annotations

import click

from gdpm import __version__


@click.group()
@click.version_option(version=__version__, prog_name="gdpm")
def main() -> None:
    """gdpm - Godot Dependency Package Manager."""


from gdpm.cli.add import add  # noqa: E402
from gdpm.cli.export import export  # noqa: E402
from gdpm.cli.info import info  # noqa: E402
from gdpm.cli.init import init  # noqa: E402
from gdpm.cli.list import list_cmd  # noqa: E402
from gdpm.cli.lock import lock  # noqa: E402
from gdpm.cli.remove import remove  # noqa: E402
from gdpm.cli.search import search  # noqa: E402
from gdpm.cli.sync import sync  # noqa: E402
from gdpm.cli.update import update  # noqa: E402

main.add_command(add)
main.add_command(export)
main.add_command(info)
main.add_command(init)
main.add_command(list_cmd, "list")
main.add_command(lock)
main.add_command(remove)
main.add_command(search)
main.add_command(sync)
main.add_command(update)
