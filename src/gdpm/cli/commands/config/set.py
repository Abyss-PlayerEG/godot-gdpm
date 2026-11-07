"""
gdpm config set 命令

- 设置一个全局配置项, 空值将该项恢复为默认.

----

Notes
----
- config_set: 校验键名与整数类型后全量写入 (所有键显式落盘).
"""

from __future__ import annotations

import click

from gdpm.cli.base import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.i18n import SUPPORTED_LANGUAGES
from gdpm.config.global_config import (
    CONFIG_FIELDS,
    GlobalConfig,
    read_global_config,
    write_global_config,
)

# 可设置字段的英文说明 (控制台输出, 与 CLI 其余输出语言一致)
_KEY_HELP: dict[str, str] = {
    "godot_path": "Godot executable path or command name",
    "addons_dir": "Plugins directory name",
    "parallel_downloads": "Parallel download count (positive integer)",
    "default_engine": "Global default engine id (empty to clear)",
    "store_url": "Asset Store API base URL",
    "cache_dir": "Download cache directory (empty to reset)",
    "language": "Help language: en/zh (empty to reset)",
}


@click.command(
    name="set",
    cls=GdpmCommand,
    examples=[
        ("gdpm config set parallel_downloads 8", "Set parallel downloads"),
        ("gdpm config set language zh", "Switch help language (en/zh)"),
        ('gdpm config set cache_dir ""', "Reset cache dir to default"),
    ],
)
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """设置全局配置项 (空值恢复该项默认)."""
    if key not in _KEY_HELP or key not in CONFIG_FIELDS:
        keys = "\n".join(f"    [bold]{k}[/bold]: {d}" for k, d in _KEY_HELP.items())
        console.print(
            f"[red]Error:[/red] Unknown config key [cyan]{key}[/cyan].\n"
            f"  Available keys:\n{keys}"
        )
        return

    config = read_global_config()
    base = GlobalConfig()

    if value == "":
        # 空值 = 恢复该项为默认 (全量写入下保留为默认值行)
        setattr(config, key, getattr(base, key))
    elif key == "parallel_downloads":
        try:
            count = int(value)
        except ValueError:
            count = -1
        if count < 1:
            console.print(
                f"[red]Error:[/red] parallel_downloads must be a positive "
                f"integer, got [cyan]{value}[/cyan]."
            )
            return
        config.parallel_downloads = count
    elif key == "language":
        if value not in SUPPORTED_LANGUAGES:
            supported = "/".join(SUPPORTED_LANGUAGES)
            console.print(
                f"[red]Error:[/red] unsupported language [cyan]{value}[/cyan]. "
                f"Supported: {supported}."
            )
            return
        config.language = value
    else:
        setattr(config, key, value)

    write_global_config(config)

    resolved = getattr(config, key)
    if resolved == getattr(base, key):
        console.print(f"[green]✓[/green] [cyan]{key}[/cyan] reset to default")
    else:
        console.print(f"[green]✓[/green] [cyan]{key}[/cyan] = [cyan]{resolved}[/cyan]")
