"""
gdpm cache 命令

- 管理全局下载缓存: 查看缓存目录/大小/插件数, 清理已缓存的插件压缩包.

----

Notes
----
- cache: 子命令组, 挂载 info 与 clean.
- cache_info: 显示缓存目录, 大小和插件数量.
- cache_clean: 清空全部缓存文件 (支持 -y 跳过确认).
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from gdpm.cache.file_cache import FileCache
from gdpm.cli.base import GdpmCommand, GdpmGroup
from gdpm.config.global_config import read_global_config

console = Console()


@click.group(
    cls=GdpmGroup,
    category="dependencies",
    examples=[
        ("gdpm cache info", "Show cache size and location"),
        ("gdpm cache clean", "Clean all cached files"),
        ("gdpm cache clean -y", "Clean without confirmation"),
    ],
)
def cache() -> None:
    """管理全局缓存."""


@cache.command(
    name="info",
    cls=GdpmCommand,
    examples=[
        ("gdpm cache info", "Show cache size and location"),
    ],
)
def cache_info() -> None:
    """显示缓存信息."""
    config = read_global_config()
    cache_dir = Path(config.cache_dir)
    file_cache = FileCache(cache_dir)

    # 人性化字节单位: B -> KB -> MB
    size = file_cache.size()
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f} MB"

    # 下载缓存按首字母分桶存放: downloads/<letter>/*.zip
    count = 0
    for letter_dir in cache_dir.glob("downloads/*/"):
        if letter_dir.is_dir():
            count += len(list(letter_dir.glob("*.zip")))

    console.print(
        f"  Cache dir:  [cyan]{cache_dir}[/cyan]\n"
        f"  Cache size: [yellow]{size_str}[/yellow]\n"
        f"  Plugins:    [green]{count}[/green]"
    )


@cache.command(
    name="clean",
    cls=GdpmCommand,
    examples=[
        ("gdpm cache clean", "Clean all cached files"),
    ],
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def cache_clean(yes: bool) -> None:
    """清理全部缓存文件."""
    config = read_global_config()
    cache_dir = Path(config.cache_dir)
    file_cache = FileCache(cache_dir)

    # 计算并格式化待清理的大小
    size = file_cache.size()
    if size == 0:
        console.print("  Cache is already empty.")
        return

    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f} MB"

    # 未指定 -y 时进行二次确认, 取消则中止
    if not yes:
        click.echo(f"  This will remove {size_str} of cached files.")
        if not click.confirm("  Continue?"):
            click.echo("  Cancelled.")
            return

    file_cache.clean()
    console.print(f"  [green]✓[/green] Cache cleaned ({size_str} freed)")
