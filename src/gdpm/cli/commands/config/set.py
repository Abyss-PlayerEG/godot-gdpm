"""
gdpm config set 命令

- 设置一个全局配置项, 空值将该项恢复为默认.

----

Notes
----
- config_set: 校验键名与整数类型后行级写入 (只动目标键行).
"""

from __future__ import annotations

from pathlib import Path

import click

from gdpm.cli.base import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.i18n import SUPPORTED_LANGUAGES
from gdpm.config.global_config import (
    CONFIG_FIELDS,
    GlobalConfig,
    set_config_value,
)
from gdpm.utils.download import MAX_SLICES

# 可设置字段的英文说明 (控制台输出, 与 CLI 其余输出语言一致)
# 只列已实现消费方的键; 未实现键 (godot_path/addons_dir/store_url) 不展示
_KEY_HELP: dict[str, str] = {
    "parallel_downloads": "Parallel download count (1-32, capped at 32)",
    "default_engine": "Global default engine id (empty to clear)",
    "cache_dir": "Download cache directory (~ expanded, empty to reset)",
    "language": "Help language: en/zh (empty to reset)",
}


@click.command(
    name="set",
    cls=GdpmCommand,
    examples=[
        (
            "gdpm config set default_engine steam-godot@4.7-stable",
            "Set default engine",
        ),
        ("gdpm config set parallel_downloads 8", "Set parallel downloads"),
        ('gdpm config set cache_dir ""', "Reset cache dir to default"),
        ("gdpm config set language zh", "Switch help language (en/zh)"),
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

    base = GlobalConfig()
    resolved: str | int

    if value == "":
        # 空值 = 恢复该项为默认 (回到默认即删行)
        resolved = getattr(base, key)
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
        # 写入端封顶: 超过 MAX_SLICES 直接按上限落盘 (与运行时收敛一致)
        resolved = min(count, MAX_SLICES)
    elif key == "language":
        if value not in SUPPORTED_LANGUAGES:
            supported = "/".join(SUPPORTED_LANGUAGES)
            console.print(
                f"[red]Error:[/red] unsupported language [cyan]{value}[/cyan]. "
                f"Supported: {supported}."
            )
            return
        resolved = value
    elif key == "cache_dir":
        # 路径类配置: 展开 ~ 并规范化为绝对路径 (直接输 ~ 是常见预期)
        resolved = str(Path(value).expanduser().absolute())
    else:
        resolved = value

    if str(resolved) == str(getattr(base, key)):
        # 行级手术: 回到默认 = 只删目标键行, 其余行一律不动
        set_config_value(key, None)
        console.print(f"[green]✓[/green] [cyan]{key}[/cyan] reset to default")
    else:
        set_config_value(key, resolved)
        console.print(f"[green]✓[/green] [cyan]{key}[/cyan] = [cyan]{resolved}[/cyan]")
