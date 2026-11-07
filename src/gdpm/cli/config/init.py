"""
gdpm config init 命令

- 恢复默认配置: 清除全部定制项.

----

Notes
----
- config_init: 稀疏存储下无定制项即无文件, 故以删除 config.toml 实现重置,
  并列出被移除的定制项.
"""

from __future__ import annotations

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.config.global_config import (
    custom_fields,
    get_config_path,
    read_global_config,
)


@click.command(
    name="init",
    cls=GdpmCommand,
    examples=[("gdpm config init", "Reset to defaults")],
)
def config_init() -> None:
    """恢复默认配置 (清除全部定制项)."""
    path = get_config_path()
    if not path.exists():
        console.print("[dim]Already at defaults (config.toml does not exist).[/dim]")
        return

    removed = ", ".join(
        f"{name}={value}" for name, value in custom_fields(read_global_config())
    )
    path.unlink()

    if removed:
        console.print(
            f"[green]✓[/green] Defaults restored (removed: [cyan]{removed}[/cyan])"
        )
    else:
        console.print("[green]✓[/green] Defaults restored")
