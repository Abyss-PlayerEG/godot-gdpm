"""
gdpm config open 命令

- 打开配置文件所在目录 (文件可能不存在, 稀疏存储下无定制项即无文件).

----

Notes
----
- config_open: 按平台打开目录 (macOS open / Windows explorer / Linux xdg-open).
"""

from __future__ import annotations

import platform
import subprocess

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.config.global_config import get_config_path


@click.command(
    name="open",
    cls=GdpmCommand,
    examples=[("gdpm config open", "Open config directory")],
)
def config_open() -> None:
    """打开配置文件所在目录."""
    config_path = get_config_path()
    target = config_path.parent
    target.mkdir(parents=True, exist_ok=True)

    system = platform.system()
    if system == "Darwin":
        cmd = ["open", str(target)]
    elif system == "Windows":
        cmd = ["explorer", str(target)]
    else:
        cmd = ["xdg-open", str(target)]

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        console.print(f"[red]Error:[/red] Failed to open directory: {e}")
        console.print(f"  Config path: [cyan]{config_path}[/cyan]")
        return

    note = (
        "config.toml missing (all defaults)"
        if not config_path.exists()
        else "config.toml"
    )
    console.print(f"[green]✓[/green] Opened [cyan]{target}[/cyan] ({note})")
