"""gdpm godot command - Godot engine management."""

from __future__ import annotations

import click

from gdpm.cli.app import GdpmGroup
from gdpm.cli.godot.engine import godot_add, godot_default, godot_remove, godot_use
from gdpm.cli.godot.info import godot_info
from gdpm.cli.godot.install import godot_install, godot_uninstall
from gdpm.cli.godot.list import godot_list
from gdpm.cli.godot.open import godot_open


@click.group(
    cls=GdpmGroup,
    examples=[
        ("gdpm godot list", "List installed Godot versions"),
        ("gdpm godot list --remote", "List available versions"),
        ("gdpm godot install 4.7", "Install Godot 4.7"),
    ],
)
def godot() -> None:
    """Manage Godot engine versions."""


godot.add_command(godot_list, "list")
godot.add_command(godot_install, "install")
godot.add_command(godot_uninstall, "uninstall")
godot.add_command(godot_add, "add")
godot.add_command(godot_remove, "remove")
godot.add_command(godot_use, "use")
godot.add_command(godot_info, "info")
godot.add_command(godot_open, "open")
godot.add_command(godot_default, "default")
